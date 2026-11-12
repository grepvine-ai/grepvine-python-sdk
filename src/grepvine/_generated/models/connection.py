from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..models.permission import Permission
from typing import cast
from uuid import UUID
import datetime


T = TypeVar("T", bound="Connection")


@_attrs_define
class Connection:
    """An app the account connected, and what it reaches and may do.

    Attributes:
        id (UUID):
        client_name (str): The name the app gave itself when it was connected.
        client_host (str): The host that serves the app's client metadata document.
        permissions (list[Permission]): The permissions a key carries, each named once.
        created_at (datetime.datetime):
        last_used_at (datetime.datetime): When the app last signed in or renewed its access.
        expires_at (datetime.datetime): When the connection stops working unless the app keeps using it.
        organization (str): An account or organization name. Accounts and organizations share one namespace. A name
            keeps the case it was created with, and any spelling that differs only in case refers to it; no other account or
            organization can take such a spelling.
        indexes (list[str]): The indexes a key reaches, by name, in the key's one organization. Omitted for every index
            of its organizations, including indexes created later. A request names at least one; a key's list is empty once
            every index it named is deleted.
    """

    id: UUID
    client_name: str
    client_host: str
    permissions: list[Permission]
    created_at: datetime.datetime
    last_used_at: datetime.datetime
    expires_at: datetime.datetime
    organization: str | None = None
    indexes: list[str] = _attrs_field(factory=list)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)
        client_name = self.client_name
        client_host = self.client_host
        permissions = []
        for componentsschemas_permissions_item_data in self.permissions:
            componentsschemas_permissions_item = componentsschemas_permissions_item_data.value
            permissions.append(componentsschemas_permissions_item)

        created_at = self.created_at.isoformat()
        last_used_at = self.last_used_at.isoformat()
        expires_at = self.expires_at.isoformat()
        _organization_value = UNSET if self.organization is None else self.organization
        organization = _organization_value
        _indexes_value = UNSET if self.indexes is None else self.indexes
        indexes: list[str] | Unset = UNSET
        if not isinstance(_indexes_value, Unset):
            indexes = _indexes_value

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "id": id,
                "client_name": client_name,
                "client_host": client_host,
                "permissions": permissions,
                "created_at": created_at,
                "last_used_at": last_used_at,
                "expires_at": expires_at,
            }
        )
        if organization is not UNSET:
            field_dict["organization"] = organization
        if indexes is not UNSET:
            field_dict["indexes"] = indexes

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = UUID(d.pop("id"))

        client_name = d.pop("client_name")

        client_host = d.pop("client_host")

        permissions = []
        _permissions = d.pop("permissions")
        for componentsschemas_permissions_item_data in _permissions:
            componentsschemas_permissions_item = Permission(componentsschemas_permissions_item_data)

            permissions.append(componentsschemas_permissions_item)

        created_at = datetime.datetime.fromisoformat(d.pop("created_at"))

        last_used_at = datetime.datetime.fromisoformat(d.pop("last_used_at"))

        expires_at = datetime.datetime.fromisoformat(d.pop("expires_at"))

        organization = d.pop("organization", UNSET)

        indexes = cast(list[str], d.pop("indexes", UNSET))

        connection = cls(
            id=id,
            client_name=client_name,
            client_host=client_host,
            permissions=permissions,
            created_at=created_at,
            last_used_at=last_used_at,
            expires_at=expires_at,
            organization=(None if isinstance(organization, Unset) else organization),
            indexes=([] if isinstance(indexes, Unset) else indexes),
        )

        return connection
