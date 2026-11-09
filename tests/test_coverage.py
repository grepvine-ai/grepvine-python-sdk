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


PAGED = {
    operation["operationId"]
    for path in SPEC["paths"].values()
    for operation in path.values()
    if isinstance(operation, dict)
    and any(
        parameter.get("$ref") == "#/components/parameters/Page"
        for parameter in operation.get("parameters", [])
    )
}
SCOPES: dict[str, dict] = json.loads((ROOT / "sdk-scopes.json").read_text())
WAITERS: dict[str, dict] = json.loads((ROOT / "sdk-waiters.json").read_text())


def calls(method: object) -> set[str]:
    """The operation modules a method sends its request through."""
    source = inspect.cleandoc("\n" + inspect.getsource(method))  # type: ignore[arg-type]
    return {
        node.value.id
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.attr in ("sync_detailed", "asyncio_detailed")
    }


def check(target: object, name: str, operation: str, is_async: bool) -> None:
    """A listing is ``name_page``, which returns one page; any other operation is ``name``."""
    method = getattr(target, f"{name}_page" if operation in PAGED else name)
    assert inspect.iscoroutinefunction(method) == is_async
    # An operation finished in the background also hands its pending object the poll operation.
    polled = {snake(WAITERS[operation]["poll"])} if operation in WAITERS else set()
    assert calls(method) == {snake(operation)} | polled


def test_paged_operations_are_the_listings() -> None:
    assert PAGED == {
        "listAPIKeys",
        "listDocuments",
        "listIndexes",
        "listOrganizationMembers",
        "listOrganizations",
        "queryIndex",
    }


@pytest.mark.parametrize("client_class", [grepvine.Client, grepvine.AsyncClient])
@pytest.mark.parametrize("operation", sorted(OPERATIONS))
def test_method_calls_its_operation(client_class: type, operation: str) -> None:
    target = client_class(trust_env=False)
    *resources, name = OPERATIONS[operation]
    for segment in resources:
        target = getattr(target, snake(segment))
    check(target, snake(name), operation, client_class is grepvine.AsyncClient)


@pytest.mark.parametrize("client_class", [grepvine.Client, grepvine.AsyncClient])
@pytest.mark.parametrize(
    ("scope", "operation"),
    sorted((scope, operation) for scope, item in SCOPES.items() for operation in item["methods"]),
)
def test_scoped_method_calls_its_operation(client_class: type, scope: str, operation: str) -> None:
    assert scope == "IndexClient"
    target = client_class(trust_env=False).index("acme/docs")
    entry = SCOPES[scope]["methods"][operation]
    name = entry if isinstance(entry, str) else entry[0]
    private = "_" if name.startswith("_") else ""
    check(
        target, private + snake(name.lstrip("_")), operation, client_class is grepvine.AsyncClient
    )


def test_index_client_covers_its_operations() -> None:
    """Every operation on one index's path is on IndexClient, and so is creating it."""
    on_index = {
        operation["operationId"]
        for path, item in SPEC["paths"].items()
        if path.startswith("/organizations/{organization}/indexes/{index}")
        for operation in item.values()
        if isinstance(operation, dict)
    }
    assert set(SCOPES["IndexClient"]["methods"]) == on_index | {"createIndex"}


def test_resources_have_no_other_operation_methods() -> None:
    expected: dict[str, set[str]] = {}
    for operation, path in OPERATIONS.items():
        methods = expected.setdefault(snake(path[-2]), set())
        name = snake(path[-1])
        methods.add(name)
        if operation in PAGED:
            methods.add(f"{name}_page")
    helpers = {
        "indexes": {"wait_until_ready"},
        "documents": {"put_many"},
        "device_login": {"authorize"},
    }
    client = grepvine.Client(trust_env=False)
    for name, methods in expected.items():
        resource = getattr(client, name, None) or client.organizations.members
        public = {
            attribute
            for attribute in dir(resource)
            if not attribute.startswith("_") and callable(getattr(resource, attribute))
        }
        assert public == methods | helpers.get(name, set()), name


def test_index_client_has_no_other_methods() -> None:
    names = set()
    for entry in SCOPES["IndexClient"]["methods"].values():
        name = entry if isinstance(entry, str) else entry[0]
        if not name.startswith("_"):
            names.add(snake(name))
    names |= {f"{name}_page" for name in ("search", "list")}
    helpers = {"put", "put_many", "wait_until_ready"}
    index = grepvine.Client(trust_env=False).index("acme/docs")
    public = {
        attribute
        for attribute in dir(index)
        if not attribute.startswith("_") and callable(getattr(index, attribute))
    }
    assert public == names | helpers


@pytest.mark.parametrize("operation", sorted(WAITERS))
def test_waiters_name_real_operations(operation: str) -> None:
    waiter = WAITERS[operation]
    assert {operation, waiter["poll"]} <= SPEC_OPERATIONS
    for prefix in ("", "Async"):
        pending = getattr(grepvine, prefix + waiter["class"])
        assert inspect.iscoroutinefunction(pending.wait) == (prefix == "Async")
