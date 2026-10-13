"""Select SDK operations and their referenced components from the source contract."""

import copy
import json
from pathlib import Path
from typing import Any

OPERATIONS = Path(__file__).resolve().parents[2] / "sdk-operations.json"
HTTP_METHODS = {"get", "put", "post", "delete", "patch", "head", "options", "trace"}


def sdk_contract(source: dict[str, Any]) -> dict[str, Any]:
    allowed = json.loads(OPERATIONS.read_text())
    if not allowed or len(allowed) != len(set(allowed)):
        raise ValueError("SDK operation allowlist must be nonempty and contain no duplicates")
    spec = copy.deepcopy(source)
    paths: dict[str, Any] = {}
    found: set[str] = set()
    tags: set[str] = set()
    for path, item in spec["paths"].items():
        selected = {}
        for method, operation in item.items():
            if method in HTTP_METHODS and operation.get("operationId") in allowed:
                selected[method] = operation
                found.add(operation["operationId"])
                tags.update(operation.get("tags", []))
        if selected:
            # Retain path-level parameters and metadata as well as selected operations.
            paths[path] = {**{k: v for k, v in item.items() if k not in HTTP_METHODS}, **selected}
    if missing := set(allowed) - found:
        raise ValueError(f"Unknown SDK operations: {sorted(missing)}")
    spec["paths"] = paths
    spec["tags"] = [tag for tag in spec.get("tags", []) if tag["name"] in tags]

    components = spec.pop("components", {})
    pending: list[str] = []
    security: set[str] = set()

    def visit(value: Any) -> None:
        if isinstance(value, dict):
            for requirement in value.get("security", []):
                security.update(requirement)
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)
        elif isinstance(value, str) and value.startswith("#/components/"):
            # Includes $ref and discriminator mapping references.
            pending.append(value)

    visit(spec)
    pending.extend(f"#/components/securitySchemes/{name}" for name in security)
    retained: dict[str, dict[str, Any]] = {}
    seen: set[str] = set()
    while pending:
        reference = pending.pop()
        tokens = [token.replace("~1", "/").replace("~0", "~") for token in reference.split("/")[2:]]
        if len(tokens) < 2:
            raise ValueError(f"Invalid component reference: {reference}")
        section, name = tokens[:2]
        component_key = f"{section}/{name}"
        if component_key in seen:
            continue
        seen.add(component_key)
        value = components[section][name]
        retained.setdefault(section, {})[name] = value
        visit(value)
    # Preserve source ordering for deterministic, readable generated output.
    spec["components"] = {
        section: {
            name: value for name, value in values.items() if name in retained.get(section, {})
        }
        for section, values in components.items()
        if section in retained
    }
    return spec


def main() -> None:
    from ruamel.yaml import YAML

    root = Path(__file__).resolve().parents[3]
    selected = sdk_contract(YAML(typ="safe").load(root / "api/openapi.yaml"))
    target = root / "tmp/sdk/openapi.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(selected, indent=2) + "\n")
    print(f"Prepared {len(json.loads(OPERATIONS.read_text()))} SDK operations")


if __name__ == "__main__":
    main()
