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


T = TypeVar("T", bound="APIKey")


@_attrs_define
class APIKey:
    """An API key, without its secret.

    Attributes:
        id (UUID): The key's unique ID.
        name (str): The name the key was given.
        prefix (str): The first characters of the key, shown to tell keys apart.
        permissions (list[Permission]): What the key may do. May be empty on a revoked key.
        created_at (datetime.datetime): When the key was created.
        organization (str): An account or organization name. Accounts and organizations share one namespace. A name
            keeps the case it was created with, and any spelling that differs only in case refers to it; no other account or
            organization can take such a spelling.
        indexes (list[str]): The indexes a key reaches, by name, in the key's one organization. Omitted for every index
            of its organizations, including indexes created later. A request names at least one; a key's list is empty once
            every index it named is deleted.
        expires_at (datetime.datetime): When the key stops working. Omitted when it never expires.
        last_used_at (datetime.datetime): When the key last authenticated a request. Omitted if it never has.
        revoked_at (datetime.datetime): When the key was revoked. Omitted while the key is active.
    """

    id: UUID
    name: str
    prefix: str
    permissions: list[Permission]
    created_at: datetime.datetime
    organization: str | None = None
    indexes: list[str] = _attrs_field(factory=list)
    expires_at: datetime.datetime | None = None
    last_used_at: datetime.datetime | None = None
    revoked_at: datetime.datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)
        name = self.name
        prefix = self.prefix
        permissions = []
        for permissions_item_data in self.permissions:
            permissions_item = permissions_item_data.value
            permissions.append(permissions_item)

        created_at = self.created_at.isoformat()
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
        _last_used_at_value = UNSET if self.last_used_at is None else self.last_used_at
        last_used_at: str | Unset = UNSET
        if not isinstance(_last_used_at_value, Unset):
            last_used_at = _last_used_at_value.isoformat()
        _revoked_at_value = UNSET if self.revoked_at is None else self.revoked_at
        revoked_at: str | Unset = UNSET
        if not isinstance(_revoked_at_value, Unset):
            revoked_at = _revoked_at_value.isoformat()

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "id": id,
                "name": name,
                "prefix": prefix,
                "permissions": permissions,
                "created_at": created_at,
            }
        )
        if organization is not UNSET:
            field_dict["organization"] = organization
        if indexes is not UNSET:
            field_dict["indexes"] = indexes
        if expires_at is not UNSET:
            field_dict["expires_at"] = expires_at
        if last_used_at is not UNSET:
            field_dict["last_used_at"] = last_used_at
        if revoked_at is not UNSET:
            field_dict["revoked_at"] = revoked_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = UUID(d.pop("id"))

        name = d.pop("name")

        prefix = d.pop("prefix")

        permissions = []
        _permissions = d.pop("permissions")
        for permissions_item_data in _permissions:
            permissions_item = Permission(permissions_item_data)

            permissions.append(permissions_item)

        created_at = datetime.datetime.fromisoformat(d.pop("created_at"))

        organization = d.pop("organization", UNSET)

        indexes = cast(list[str], d.pop("indexes", UNSET))

        _expires_at = d.pop("expires_at", UNSET)
        expires_at: datetime.datetime | Unset
        if isinstance(_expires_at, Unset):
            expires_at = UNSET
        else:
            expires_at = datetime.datetime.fromisoformat(_expires_at)

        _last_used_at = d.pop("last_used_at", UNSET)
        last_used_at: datetime.datetime | Unset
        if isinstance(_last_used_at, Unset):
            last_used_at = UNSET
        else:
            last_used_at = datetime.datetime.fromisoformat(_last_used_at)

        _revoked_at = d.pop("revoked_at", UNSET)
        revoked_at: datetime.datetime | Unset
        if isinstance(_revoked_at, Unset):
            revoked_at = UNSET
        else:
            revoked_at = datetime.datetime.fromisoformat(_revoked_at)

        api_key = cls(
            id=id,
            name=name,
            prefix=prefix,
            permissions=permissions,
            created_at=created_at,
            organization=(None if isinstance(organization, Unset) else organization),
            indexes=([] if isinstance(indexes, Unset) else indexes),
            expires_at=(None if isinstance(expires_at, Unset) else expires_at),
            last_used_at=(None if isinstance(last_used_at, Unset) else last_used_at),
            revoked_at=(None if isinstance(revoked_at, Unset) else revoked_at),
        )

        return api_key
