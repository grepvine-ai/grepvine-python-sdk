"""Generate from the sole API contract, with two equivalent generator adaptations."""

import hashlib
import json
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


def main() -> None:
    yaml = YAML()
    provenance = json.loads((PACKAGE / "spec/source.json").read_text())
    if hashlib.sha256(SNAPSHOT.read_bytes()).hexdigest() != provenance["snapshot_sha256"]:
        sys.exit("Snapshot checksum does not match spec/source.json")
    spec = yaml.load(SPEC)
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
        templates = temporary / "templates"
        templates.mkdir()
        (templates / "endpoint_macros.py.jinja").write_text(
            template.replace(statement, statement + ".read()")
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
            check=True,
        )
        # The generator can exit successfully after omitting unsupported operations.
        if "WARNING" in result.stdout + result.stderr:
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
        subprocess.run(["ruff", "check", "--fix", "--isolated", str(generated)], check=True)
        subprocess.run(
            ["ruff", "format", "--isolated", "--line-length", "100", str(generated)], check=True
        )
        shutil.rmtree(OUTPUT, ignore_errors=True)
        shutil.copytree(generated, OUTPUT)
        print(f"Generated {actual} Python operations from {SPEC.name}")


if __name__ == "__main__":
    main()
