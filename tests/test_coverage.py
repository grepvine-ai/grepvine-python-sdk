"""Every API operation has exactly one home on the client.

``spec/source.json`` lists the operations of the API. Each one must be called
by exactly one function in ``grepvine_sdk._core.ops`` (the only module that
calls API operations), and that function must be used by exactly one public
method of the synchronous client's resources and one of the asynchronous
client's. A new operation therefore fails this test until it has a method.
"""

from __future__ import annotations

import ast
import json
import re
from collections import defaultdict
from functools import cache
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "src" / "grepvine_sdk"
OPERATIONS: list[str] = json.loads((ROOT / "spec" / "source.json").read_text())["operations"]
API_PREFIX = "grepvine_sdk._generated.api."


def _module_name(operation_id: str) -> str:
    """The generated module of an operation: ``listAPIKeys`` is ``list_api_keys``."""
    words = re.sub(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])", "_", operation_id)
    return words.lower()


def _api_imports(tree: ast.Module) -> set[str]:
    return {
        alias.asname or alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and (node.module or "").startswith(API_PREFIX)
        for alias in node.names
    }


@cache
def _homes() -> dict[str, list[str]]:
    """Each API operation module, with the ops functions that call it."""
    tree = ast.parse((PACKAGE / "_core" / "ops.py").read_text())
    modules = _api_imports(tree)
    homes: dict[str, list[str]] = defaultdict(list)
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            used = {n.id for n in ast.walk(node) if isinstance(n, ast.Name) and n.id in modules}
            for module in used:
                homes[module].append(node.name)
    return homes


@cache
def _callers(flavor: str) -> dict[str, list[str]]:
    """Each ops function, with the resource methods of one client flavor that use it."""
    tree = ast.parse((PACKAGE / flavor / "resources.py").read_text())
    callers: dict[str, list[str]] = defaultdict(list)
    for cls in tree.body:
        if not isinstance(cls, ast.ClassDef):
            continue
        for method in cls.body:
            if not isinstance(method, ast.FunctionDef | ast.AsyncFunctionDef):
                continue
            used = {
                n.attr
                for n in ast.walk(method)
                if isinstance(n, ast.Attribute)
                and isinstance(n.value, ast.Name)
                and n.value.id == "ops"
            }
            for function in used:
                callers[function].append(f"{cls.name}.{method.name}")
    return callers


def test_operation_ids_map_to_generated_modules() -> None:
    assert _module_name("listAPIKeys") == "list_api_keys"
    assert _module_name("revokeAPIKey") == "revoke_api_key"
    assert _module_name("getUsernameAvailability") == "get_username_availability"
    generated = {path.stem for path in (PACKAGE / "_generated" / "api").rglob("*.py")}
    assert {_module_name(op) for op in OPERATIONS} <= generated


def test_only_ops_calls_api_operations() -> None:
    for path in PACKAGE.rglob("*.py"):
        if "_generated" in path.parts or path.name == "ops.py":
            continue
        assert not _api_imports(ast.parse(path.read_text())), path


def test_no_operation_outside_the_spec_is_called() -> None:
    assert set(_homes()) <= {_module_name(op) for op in OPERATIONS}


@pytest.mark.parametrize("operation_id", OPERATIONS)
@pytest.mark.parametrize("flavor", ["_sync", "_async"])
def test_every_operation_has_exactly_one_method(operation_id: str, flavor: str) -> None:
    homes = _homes().get(_module_name(operation_id), [])
    assert len(homes) == 1, f"{operation_id} is called by {homes or 'no function'} in ops.py"
    methods = _callers(flavor).get(homes[0], [])
    assert len(methods) == 1, f"{operation_id} ({homes[0]}) is used by {methods or 'no method'}"
    assert not methods[0].split(".")[1].startswith("_"), methods[0]
