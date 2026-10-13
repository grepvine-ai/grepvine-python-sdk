"""Check the supported public surface, including every public API operation."""

import importlib
import pkgutil

import grepvine_sdk.generated.api as api


def test_sdk_contains_all_public_api_sections() -> None:
    assert {module.name for module in pkgutil.iter_modules(api.__path__)} == {
        "authentication",
        "api_keys",
        "organizations",
        "device_login",
        "indexes",
        "objects",
        "search",
    }
    expected = {
        "authentication": {
            "register_user",
            "get_username_availability",
            "login",
            "logout",
            "get_current_user",
            "change_password",
        },
        "api_keys": {"list_api_keys", "create_api_key", "revoke_api_key"},
        "organizations": {
            "list_organizations",
            "create_organization",
            "get_organization",
            "delete_organization",
            "list_organization_members",
            "add_organization_member",
            "update_organization_member",
            "remove_organization_member",
            "transfer_organization_ownership",
        },
        "device_login": {
            "start_device_authorization",
            "poll_device_token",
            "approve_device_authorization",
            "deny_device_authorization",
        },
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
