from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..types import UNSET, Unset

from ..models.role import Role
from uuid import UUID
import datetime


T = TypeVar("T", bound="Organization")


@_attrs_define
class Organization:
    """An organization, as seen by one of its members.

    Attributes:
        id (UUID): The organization's unique ID.
        name (str): A name: of an account, an organization or an agent. Accounts and organizations share one namespace;
            an agent's name is unique within its organization. A name keeps the case it was created with, and any spelling
            that differs only in case refers to it; nothing else in the same namespace can take such a spelling.
        suspended (bool): A suspended organization keeps its data, but refuses every operation on its members, indexes,
            documents and searches until it is resumed. Contact support.
        members_create_agents (bool): Whether developers can create agents, as owners and admins always can.
        created_at (datetime.datetime): When the organization was created.
        role (Role): A member's role in an organization. `owner` can do everything, including deleting the organization
            and transferring ownership; `admin` also manages members and indexes; `developer` reads, writes and searches
            documents; `reader` reads and searches them.
    """

    id: UUID
    name: str
    suspended: bool
    members_create_agents: bool
    created_at: datetime.datetime
    role: Role | None = None

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)
        name = self.name
        suspended = self.suspended
        members_create_agents = self.members_create_agents
        created_at = self.created_at.isoformat()
        _role_value = UNSET if self.role is None else self.role
        role: str | Unset = UNSET
        if not isinstance(_role_value, Unset):
            role = _role_value.value

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "id": id,
                "name": name,
                "suspended": suspended,
                "members_create_agents": members_create_agents,
                "created_at": created_at,
            }
        )
        if role is not UNSET:
            field_dict["role"] = role

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = UUID(d.pop("id"))

        name = d.pop("name")

        suspended = d.pop("suspended")

        members_create_agents = d.pop("members_create_agents")

        created_at = datetime.datetime.fromisoformat(d.pop("created_at"))

        _role = d.pop("role", UNSET)
        role: Role | Unset
        if isinstance(_role, Unset):
            role = UNSET
        else:
            role = Role(_role)

        organization = cls(
            id=id,
            name=name,
            suspended=suspended,
            members_create_agents=members_create_agents,
            created_at=created_at,
            role=(None if isinstance(role, Unset) else role),
        )

        return organization
