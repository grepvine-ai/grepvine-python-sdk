from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..models.permission import Permission
from typing import cast
import datetime


T = TypeVar("T", bound="PendingDeviceAuthorization")


@_attrs_define
class PendingDeviceAuthorization:
    """What a pending device authorization asks for.

    Attributes:
        api_key_name (str): The name the key the device receives will have.
        permissions (list[Permission]): The permissions a key carries, each named once.
        organization (str): An account or organization name. Accounts and organizations share one namespace. A name
            keeps the case it was created with, and any spelling that differs only in case refers to it; no other account or
            organization can take such a spelling.
        indexes (list[str]): The indexes a key reaches, by name, in the key's one organization. Omitted for every index
            of its organizations, including indexes created later. A request names at least one; a key's list is empty once
            every index it named is deleted.
        expires_at (datetime.datetime): When the key the device receives stops working. Omitted when it never expires.
    """

    api_key_name: str
    permissions: list[Permission]
    organization: str | None = None
    indexes: list[str] = _attrs_field(factory=list)
    expires_at: datetime.datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        api_key_name = self.api_key_name
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

        _expires_at_value = UNSET if self.expires_at is None else self.expires_at
        expires_at: str | Unset = UNSET
        if not isinstance(_expires_at_value, Unset):
            expires_at = _expires_at_value.isoformat()

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "api_key_name": api_key_name,
                "permissions": permissions,
            }
        )
        if organization is not UNSET:
            field_dict["organization"] = organization
        if indexes is not UNSET:
            field_dict["indexes"] = indexes
        if expires_at is not UNSET:
            field_dict["expires_at"] = expires_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        api_key_name = d.pop("api_key_name")

        permissions = []
        _permissions = d.pop("permissions")
        for componentsschemas_permissions_item_data in _permissions:
            componentsschemas_permissions_item = Permission(componentsschemas_permissions_item_data)

            permissions.append(componentsschemas_permissions_item)

        organization = d.pop("organization", UNSET)

        indexes = cast(list[str], d.pop("indexes", UNSET))

        _expires_at = d.pop("expires_at", UNSET)
        expires_at: datetime.datetime | Unset
        if isinstance(_expires_at, Unset):
            expires_at = UNSET
        else:
            expires_at = datetime.datetime.fromisoformat(_expires_at)

        pending_device_authorization = cls(
            api_key_name=api_key_name,
            permissions=permissions,
            organization=(None if isinstance(organization, Unset) else organization),
            indexes=([] if isinstance(indexes, Unset) else indexes),
            expires_at=(None if isinstance(expires_at, Unset) else expires_at),
        )

        return pending_device_authorization
