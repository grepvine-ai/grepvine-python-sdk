"""Check the supported public surface, including the absence of management APIs."""

import importlib
import pkgutil

import grepvine_sdk.generated.api as api


def test_sdk_contains_only_cli_api_sections() -> None:
    assert {module.name for module in pkgutil.iter_modules(api.__path__)} == {
        "device_login",
        "indexes",
        "objects",
        "search",
    }
    expected = {
        "device_login": {"start_device_authorization", "poll_device_token"},
        "indexes": {"list_indexes", "create_index", "get_index", "update_index", "delete_index"},
        "objects": {
            "list_documents",
            "put_document",
            "get_document",
            "delete_document",
            "put_objects",
            "delete_objects",
        },
        "search": {"query_index"},
    }
    for section, operations in expected.items():
        module = importlib.import_module(f"{api.__name__}.{section}")
        assert {entry.name for entry in pkgutil.iter_modules(module.__path__)} == operations
        for name in operations:
            operation = importlib.import_module(f"{module.__name__}.{name}")
            assert callable(operation.sync_detailed)
            assert callable(operation.asyncio_detailed)
