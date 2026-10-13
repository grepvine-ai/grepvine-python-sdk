from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..types import UNSET, Unset

from uuid import UUID
import datetime


T = TypeVar("T", bound="APIKey")


@_attrs_define
class APIKey:
    """
    Attributes:
        id (UUID):
        name (str):
        prefix (str):
        created_at (datetime.datetime):
        last_used_at (datetime.datetime | Unset):
        revoked_at (datetime.datetime | Unset):
    """

    id: UUID
    name: str
    prefix: str
    created_at: datetime.datetime
    last_used_at: datetime.datetime | Unset = UNSET
    revoked_at: datetime.datetime | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        name = self.name

        prefix = self.prefix

        created_at = self.created_at.isoformat()

        last_used_at: str | Unset = UNSET
        if not isinstance(self.last_used_at, Unset):
            last_used_at = self.last_used_at.isoformat()

        revoked_at: str | Unset = UNSET
        if not isinstance(self.revoked_at, Unset):
            revoked_at = self.revoked_at.isoformat()

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "id": id,
                "name": name,
                "prefix": prefix,
                "created_at": created_at,
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
            created_at=created_at,
            last_used_at=last_used_at,
            revoked_at=revoked_at,
        )

        return api_key
