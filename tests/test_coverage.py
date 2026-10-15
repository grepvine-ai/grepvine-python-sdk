"""Every API operation has exactly one method on both clients, named by sdk-operations.json."""

from __future__ import annotations

import ast
import inspect
import json
import re
from pathlib import Path

import pytest

import grepvine

ROOT = Path(__file__).resolve().parents[1]
OPERATIONS: dict[str, list[str]] = json.loads((ROOT / "sdk-operations.json").read_text())
SPEC = json.loads((ROOT / "spec/openapi.json").read_text())
SPEC_OPERATIONS = {
    operation["operationId"]
    for path in SPEC["paths"].values()
    for operation in path.values()
    if isinstance(operation, dict) and "operationId" in operation
}


def snake(name: str) -> str:
    """``transferOwnership`` is ``transfer_ownership``; ``listAPIKeys`` is ``list_api_keys``."""
    return re.sub(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])", "_", name).lower()


def test_map_covers_exactly_the_api() -> None:
    assert set(OPERATIONS) == SPEC_OPERATIONS
    assert set(json.loads((ROOT / "spec/source.json").read_text())["operations"]) == SPEC_OPERATIONS


def test_each_method_is_used_once() -> None:
    paths = [tuple(path) for path in OPERATIONS.values()]
    assert len(set(paths)) == len(paths)


@pytest.mark.parametrize("client_class", [grepvine.Client, grepvine.AsyncClient])
@pytest.mark.parametrize("operation", sorted(OPERATIONS))
def test_method_calls_its_operation(client_class: type, operation: str) -> None:
    client = client_class()
    target = client
    for segment in OPERATIONS[operation]:
        target = getattr(target, snake(segment))
    assert inspect.iscoroutinefunction(target) == (client_class is grepvine.AsyncClient)
    source = inspect.getsource(target)
    called = {
        node.func.value.id
        for node in ast.walk(ast.parse(inspect.cleandoc("\n" + source)))
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.attr in ("sync_detailed", "asyncio_detailed")
    }
    assert called == {snake(operation)}


def test_resources_have_no_other_operation_methods() -> None:
    expected: dict[str, set[str]] = {}
    for path in OPERATIONS.values():
        expected.setdefault(snake(path[-2]), set()).add(snake(path[-1]))
    helpers = {
        "indexes": {"wait_until_ready"},
        "documents": {"put_many"},
        "device_login": {"authorize"},
    }
    client = grepvine.Client()
    for name, methods in expected.items():
        resource = getattr(client, name, None) or client.organizations.members
        public = {
            attribute
            for attribute in dir(resource)
            if not attribute.startswith("_") and callable(getattr(resource, attribute))
        }
        assert public == methods | helpers.get(name, set()), name
