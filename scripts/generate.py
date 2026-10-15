"""Generate the private package from the API contract and the resource naming map."""

import hashlib
import json
import re
import shutil
import subprocess
import sys
from importlib.resources import files
from pathlib import Path
from tempfile import TemporaryDirectory

from ruamel.yaml import YAML

PACKAGE = Path(__file__).resolve().parents[1]
SNAPSHOT = PACKAGE / "spec/openapi.json"
SPEC = SNAPSHOT
OUTPUT = PACKAGE / "src/grepvine/_generated"
OPERATIONS = PACKAGE / "sdk-operations.json"
TEMPLATES = PACKAGE / "scripts/templates"
# Docstrings of the resource classes; a resource missing here gets one from its name.
TITLES = {
    "organizations": "Organizations: create, read, delete and transfer them.",
    "organizations.members": "The members of an organization and their roles.",
    "indexes": "Indexes in an organization.",
    "documents": "The documents of an index.",
    "search": "Search over the documents of an index.",
    "apiKeys": "The API keys of the signed-in user.",
    "account": "User accounts: registration, sign-in and the current user.",
    "deviceLogin": "Device login: obtain an API key by approving a code in the browser.",
}


def words(segment: str) -> list[str]:
    return re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", segment).lower().split()


def resources(operations: dict[str, list[str]]) -> tuple[list[dict], list[list[str]]]:
    """Resource classes from the naming map, nested ones first, and the client's attributes."""
    tree: dict[tuple[str, ...], dict] = {}
    for operation, path in operations.items():
        *parents, method = path
        for depth in range(1, len(parents) + 1):
            prefix = tuple(parents[:depth])
            if prefix not in tree:
                name = "".join(
                    "API" if word == "api" else word.capitalize() for word in words(prefix[-1])
                )
                title = TITLES.get(".".join(prefix), f"The {' '.join(words(prefix[-1]))}.")
                tree[prefix] = {"name": name, "title": title, "methods": [], "children": []}
                if depth > 1:
                    tree[prefix[:-1]]["children"].append(["_".join(words(prefix[-1])), name])
        tree[tuple(parents)]["methods"].append(["_".join(words(method)), operation])
    names = [item["name"] for item in tree.values()]
    if len(set(names)) != len(names):
        sys.exit(f"Resource class names collide: {sorted(names)}")
    ordered = sorted(tree.items(), key=lambda item: -len(item[0]))
    roots = [
        ["_".join(words(path[0])), item["name"]] for path, item in tree.items() if len(path) == 1
    ]
    return [item for _, item in ordered], roots


def main() -> None:
    yaml = YAML()
    provenance = json.loads((PACKAGE / "spec/source.json").read_text())
    if hashlib.sha256(SNAPSHOT.read_bytes()).hexdigest() != provenance["snapshot_sha256"]:
        sys.exit("Snapshot checksum does not match spec/source.json")
    spec = yaml.load(SPEC)
    operations = json.loads(OPERATIONS.read_text())
    operation_ids = {
        operation["operationId"]
        for path in spec["paths"].values()
        for operation in path.values()
        if isinstance(operation, dict) and "operationId" in operation
    }
    if unmapped := sorted(operation_ids - set(operations)):
        sys.exit(f"Add these operations to {OPERATIONS.name}: {unmapped}")
    if stale := sorted(set(operations) - operation_ids):
        sys.exit(f"{OPERATIONS.name} names operations the API does not have: {stale}")
    # 0.29.1 rejects const headers. A singleton enum accepts exactly the same value.
    header = spec["components"]["parameters"]["IfNoneMatch"]["schema"]
    assert header["const"] == "*"
    header["enum"] = [header.pop("const")]
    # Represent the raw NDJSON request as File/bytes, preserving the original media type.
    body = spec["paths"]["/organizations/{organization}/indexes/{index}/objects:batch"]["post"][
        "requestBody"
    ]["content"]["application/x-ndjson"]["schema"]
    assert body["type"] == "string" and "format" not in body
    body["format"] = "binary"
    # The client adds an Idempotency-Key to every write and sends the session's CSRF token
    # itself, so neither is a required argument of a method.
    spec["components"]["parameters"]["IdempotencyKey"]["required"] = False
    for path in spec["paths"].values():
        for operation in path.values():
            if isinstance(operation, dict) and "parameters" in operation:
                operation["parameters"] = [
                    parameter
                    for parameter in operation["parameters"]
                    if parameter.get("$ref") != "#/components/parameters/CSRFToken"
                ]

    with TemporaryDirectory(prefix="grepvine-python-sdk-") as directory:
        temporary = Path(directory)
        adapted = temporary / "openapi.yaml"
        with adapted.open("w") as target:
            yaml.dump(spec, target)
        generated = temporary / "generated"
        # HTTPX AsyncClient cannot send a synchronous BinaryIO as raw content.
        # Buffer the bounded NDJSON body in the generator template for both modes.
        template = (
            files("openapi_python_client")
            .joinpath("templates/endpoint_macros.py.jinja")
            .read_text()
        )
        statement = '_kwargs["content"] = body.payload'
        if template.count(statement) != 2:
            sys.exit("Review the raw-body adapter after changing the generator version")
        # Methods raise the SDK's errors rather than the generator's.
        raises = template[template.index("Raises:") : template.index("Returns:")]
        if template.count(raises) != 1 or "UnexpectedStatus" not in raises:
            sys.exit("Review the docstring adapter after changing the generator version")
        template = template.replace(
            raises,
            "Raises:\n"
            "    grepvine.APIError: The service answered with an error.\n"
            "    grepvine.TransportError: The request could not be delivered.\n\n",
        )
        templates = temporary / "templates"
        shutil.copytree(TEMPLATES, templates)
        (templates / "endpoint_macros.py.jinja").write_text(
            template.replace(statement, statement + ".read()")
        )
        tree, roots = resources(operations)
        (templates / "sdk_resources.jinja").write_text(
            f"{{% set resources = {json.dumps(tree)} %}}\n{{% set roots = {json.dumps(roots)} %}}\n"
        )
        result = subprocess.run(
            [
                "openapi-python-client",
                "generate",
                "--path",
                str(adapted),
                "--config",
                str(PACKAGE / "openapi-python-client.yaml"),
                "--custom-template-path",
                str(templates),
                "--meta",
                "none",
                "--output-path",
                str(generated),
            ],
            text=True,
            capture_output=True,
        )
        # The generator can exit successfully after omitting unsupported operations.
        if result.returncode or "WARNING" in result.stdout + result.stderr:
            sys.exit(result.stdout + result.stderr)
        expected = sum(
            "operationId" in operation
            for path in spec["paths"].values()
            for operation in path.values()
            if isinstance(operation, dict)
        )
        actual = len([p for p in (generated / "api").rglob("*.py") if p.name != "__init__.py"])
        if actual != expected:
            sys.exit(f"Expected {expected} generated operations, got {actual}")
        # The resource classes render through the generator's api/__init__.py template. They move
        # to api/resources.py (same package, so the relative imports hold), where ruff can drop the
        # imports no method uses.
        api_init = generated / "api/__init__.py"
        api_init.rename(generated / "api/resources.py")
        api_init.write_text('"""Contains methods for accessing the API"""\n')
        subprocess.run(["ruff", "check", "--fix", "--isolated", str(generated)], check=True)
        subprocess.run(
            ["ruff", "format", "--isolated", "--line-length", "100", str(generated)], check=True
        )
        shutil.rmtree(OUTPUT, ignore_errors=True)
        shutil.copytree(generated, OUTPUT)
        print(f"Generated {actual} Python operations from {SPEC.name}")


if __name__ == "__main__":
    main()
