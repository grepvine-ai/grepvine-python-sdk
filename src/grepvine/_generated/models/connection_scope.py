from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..models.permission import Permission
from typing import cast


T = TypeVar("T", bound="ConnectionScope")


@_attrs_define
class ConnectionScope:
    """What a connection reaches and may do. A field left out sets no limit.

    Attributes:
        permissions (list[Permission]): The permissions a key carries, each named once.
        organization (str): An account or organization name. Accounts and organizations share one namespace. A name
            keeps the case it was created with, and any spelling that differs only in case refers to it; no other account or
            organization can take such a spelling.
        indexes (list[str]): The indexes a key reaches, by name, in the key's one organization. Omitted for every index
            of its organizations, including indexes created later. A request names at least one; a key's list is empty once
            every index it named is deleted.
    """

    permissions: list[Permission]
    organization: str | None = None
    indexes: list[str] = _attrs_field(factory=list)

    def to_dict(self) -> dict[str, Any]:
        permissions = []
        for componentsschemas_permissions_item_data in self.permissions:
            componentsschemas_permissions_item = componentsschemas_permissions_item_data.value
            permissions.append(componentsschemas_permissions_item)

        _organization_value = UNSET if self.organization is None else self.organization
        organization = _organization_value
        _indexes_value = UNSET if self.indexes is None else self.indexes
        indexes: list[str] | Unset = UNSET
        if not isinstance(_indexes_value, Unset):
            indexes = _indexes_value

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "permissions": permissions,
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
        permissions = []
        _permissions = d.pop("permissions")
        for componentsschemas_permissions_item_data in _permissions:
            componentsschemas_permissions_item = Permission(componentsschemas_permissions_item_data)

            permissions.append(componentsschemas_permissions_item)

        organization = d.pop("organization", UNSET)

        indexes = cast(list[str], d.pop("indexes", UNSET))

        connection_scope = cls(
            permissions=permissions,
            organization=(None if isinstance(organization, Unset) else organization),
            indexes=([] if isinstance(indexes, Unset) else indexes),
        )

        return connection_scope
