from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define


from ..models.permission import Permission


T = TypeVar("T", bound="PendingOAuthAuthorization")


@_attrs_define
class PendingOAuthAuthorization:
    """Who an app signing in is and what it asks for. The name is the app's own and is not verified; the host is where its
    metadata document is served.

        Attributes:
            client_name (str): The name the app gives itself.
            client_host (str): The host that serves the app's client metadata document.
            redirect_host (str): The host the answer is sent to.
            loopback_redirect (bool): Whether the answer is sent to this computer, as a desktop or command-line app receives
                it.
            permissions (list[Permission]): The permissions a key carries, each named once.
    """

    client_name: str
    client_host: str
    redirect_host: str
    loopback_redirect: bool
    permissions: list[Permission]

    def to_dict(self) -> dict[str, Any]:
        client_name = self.client_name
        client_host = self.client_host
        redirect_host = self.redirect_host
        loopback_redirect = self.loopback_redirect
        permissions = []
        for componentsschemas_permissions_item_data in self.permissions:
            componentsschemas_permissions_item = componentsschemas_permissions_item_data.value
            permissions.append(componentsschemas_permissions_item)

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "client_name": client_name,
                "client_host": client_host,
                "redirect_host": redirect_host,
                "loopback_redirect": loopback_redirect,
                "permissions": permissions,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        client_name = d.pop("client_name")

        client_host = d.pop("client_host")

        redirect_host = d.pop("redirect_host")

        loopback_redirect = d.pop("loopback_redirect")

        permissions = []
        _permissions = d.pop("permissions")
        for componentsschemas_permissions_item_data in _permissions:
            componentsschemas_permissions_item = Permission(componentsschemas_permissions_item_data)

            permissions.append(componentsschemas_permissions_item)

        pending_o_auth_authorization = cls(
            client_name=client_name,
            client_host=client_host,
            redirect_host=redirect_host,
            loopback_redirect=loopback_redirect,
            permissions=permissions,
        )

        return pending_o_auth_authorization
