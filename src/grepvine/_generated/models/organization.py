from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define


from ..models.role import Role
from uuid import UUID
import datetime


T = TypeVar("T", bound="Organization")


@_attrs_define
class Organization:
    """
    Attributes:
        id (UUID):
        name (str): An account or organization name. Accounts and organizations share one namespace. A name keeps the
            case it was created with, and any spelling that differs only in case refers to it; no other account or
            organization can take such a spelling.
        role (Role):
        created_at (datetime.datetime):
    """

    id: UUID
    name: str
    role: Role
    created_at: datetime.datetime

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        name = self.name

        role = self.role.value

        created_at = self.created_at.isoformat()

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "id": id,
                "name": name,
                "role": role,
                "created_at": created_at,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = UUID(d.pop("id"))

        name = d.pop("name")

        role = Role(d.pop("role"))

        created_at = datetime.datetime.fromisoformat(d.pop("created_at"))

        organization = cls(
            id=id,
            name=name,
            role=role,
            created_at=created_at,
        )

        return organization
