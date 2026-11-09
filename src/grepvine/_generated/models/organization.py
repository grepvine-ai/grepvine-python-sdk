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
    """An organization, as seen by one of its members.

    Attributes:
        id (UUID): The organization's unique ID.
        name (str): An account or organization name. Accounts and organizations share one namespace. A name keeps the
            case it was created with, and any spelling that differs only in case refers to it; no other account or
            organization can take such a spelling.
        role (Role): A member's role in an organization. `owner` can do everything, including deleting the organization
            and transferring ownership; `admin` also manages members and indexes; `developer` reads, writes and searches
            documents; `reader` reads and searches them.
        suspended (bool): A suspended organization keeps its data, but refuses every operation on its members, indexes,
            documents and searches until it is resumed. Contact support.
        created_at (datetime.datetime): When the organization was created.
    """

    id: UUID
    name: str
    role: Role
    suspended: bool
    created_at: datetime.datetime

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        name = self.name

        role = self.role.value

        suspended = self.suspended

        created_at = self.created_at.isoformat()

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "id": id,
                "name": name,
                "role": role,
                "suspended": suspended,
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

        suspended = d.pop("suspended")

        created_at = datetime.datetime.fromisoformat(d.pop("created_at"))

        organization = cls(
            id=id,
            name=name,
            role=role,
            suspended=suspended,
            created_at=created_at,
        )

        return organization
