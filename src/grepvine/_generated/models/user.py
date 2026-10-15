from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define


from uuid import UUID
import datetime


T = TypeVar("T", bound="User")


@_attrs_define
class User:
    """
    Attributes:
        id (UUID):
        name (str): An account or organization name. Accounts and organizations share one namespace. A name keeps the
            case it was created with, and any spelling that differs only in case refers to it; no other account or
            organization can take such a spelling.
        email (str):
        created_at (datetime.datetime):
    """

    id: UUID
    name: str
    email: str
    created_at: datetime.datetime

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        name = self.name

        email = self.email

        created_at = self.created_at.isoformat()

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "id": id,
                "name": name,
                "email": email,
                "created_at": created_at,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = UUID(d.pop("id"))

        name = d.pop("name")

        email = d.pop("email")

        created_at = datetime.datetime.fromisoformat(d.pop("created_at"))

        user = cls(
            id=id,
            name=name,
            email=email,
            created_at=created_at,
        )

        return user
