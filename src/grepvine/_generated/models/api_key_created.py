from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from uuid import UUID
import datetime


T = TypeVar("T", bound="APIKeyCreated")


@_attrs_define
class APIKeyCreated:
    """A new API key with its secret, which is shown only this once.

    Attributes:
        id (UUID): The key's unique ID.
        name (str): The name the key was given.
        prefix (str): The first characters of the key, shown to tell keys apart.
        created_at (datetime.datetime): When the key was created.
        key (str): The secret API key. It is shown only in this response; send it as `Authorization: Bearer <key>`.
        last_used_at (datetime.datetime): When the key last authenticated a request. Omitted if it never has.
        revoked_at (datetime.datetime): When the key was revoked. Omitted while the key is active.
    """

    id: UUID
    name: str
    prefix: str
    created_at: datetime.datetime
    key: str
    last_used_at: datetime.datetime | None = None
    revoked_at: datetime.datetime | None = None
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)
        name = self.name
        prefix = self.prefix
        created_at = self.created_at.isoformat()
        key = self.key
        _last_used_at_value = UNSET if self.last_used_at is None else self.last_used_at
        last_used_at: str | Unset = UNSET
        if not isinstance(_last_used_at_value, Unset):
            last_used_at = _last_used_at_value.isoformat()
        _revoked_at_value = UNSET if self.revoked_at is None else self.revoked_at
        revoked_at: str | Unset = UNSET
        if not isinstance(_revoked_at_value, Unset):
            revoked_at = _revoked_at_value.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "prefix": prefix,
                "created_at": created_at,
                "key": key,
            }
        )
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

        created_at = datetime.datetime.fromisoformat(d.pop("created_at"))

        key = d.pop("key")

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

        api_key_created = cls(
            id=id,
            name=name,
            prefix=prefix,
            created_at=created_at,
            key=key,
            last_used_at=(None if isinstance(last_used_at, Unset) else last_used_at),
            revoked_at=(None if isinstance(revoked_at, Unset) else revoked_at),
        )

        api_key_created.additional_properties = d
        return api_key_created

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
