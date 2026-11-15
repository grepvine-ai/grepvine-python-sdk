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


T = TypeVar("T", bound="Agent")


@_attrs_define
class Agent:
    """An agent of an organization: what it reaches and may do, and who manages it.

    Attributes:
        id (UUID):
        name (str): A name: of an account, an organization or an agent. Accounts and organizations share one namespace;
            an agent's name is unique within its organization. A name keeps the case it was created with, and any spelling
            that differs only in case refers to it; nothing else in the same namespace can take such a spelling.
        description (str): What the agent is for, at most 1,024 characters.
        permissions (list[Permission]): What an agent may do, each named once: `search`, `read`, `write`, `create_index`
            and `manage_index`, as for a key. `create_index` needs every index.
        managers (list[str]): The accounts that manage the agent, by name.
        created_at (datetime.datetime):
        disabled (bool): Whether the agent is disabled: every request it makes is refused.
        needs_review (bool): Whether the agent's permissions should be reviewed, because a manager left or lost a role.
        indexes (list[str]): The indexes a key reaches, by name, in the key's one organization. Omitted for every index
            of its organizations, including indexes created later. A request names at least one; a key's list is empty once
            every index it named is deleted.
        created_by (str): A name: of an account, an organization or an agent. Accounts and organizations share one
            namespace; an agent's name is unique within its organization. A name keeps the case it was created with, and any
            spelling that differs only in case refers to it; nothing else in the same namespace can take such a spelling.
        last_used_at (datetime.datetime): When the agent last authenticated a request. Omitted if it never has.
    """

    id: UUID
    name: str
    description: str
    permissions: list[Permission]
    managers: list[str]
    created_at: datetime.datetime
    disabled: bool
    needs_review: bool
    indexes: list[str] = _attrs_field(factory=list)
    created_by: str | None = None
    last_used_at: datetime.datetime | None = None
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)
        name = self.name
        description = self.description
        permissions = []
        for componentsschemas_agent_permissions_item_data in self.permissions:
            componentsschemas_agent_permissions_item = (
                componentsschemas_agent_permissions_item_data.value
            )
            permissions.append(componentsschemas_agent_permissions_item)

        managers = self.managers

        created_at = self.created_at.isoformat()
        disabled = self.disabled
        needs_review = self.needs_review
        _indexes_value = UNSET if self.indexes is None else self.indexes
        indexes: list[str] | Unset = UNSET
        if not isinstance(_indexes_value, Unset):
            indexes = _indexes_value

        _created_by_value = UNSET if self.created_by is None else self.created_by
        created_by = _created_by_value
        _last_used_at_value = UNSET if self.last_used_at is None else self.last_used_at
        last_used_at: str | Unset = UNSET
        if not isinstance(_last_used_at_value, Unset):
            last_used_at = _last_used_at_value.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "description": description,
                "permissions": permissions,
                "managers": managers,
                "created_at": created_at,
                "disabled": disabled,
                "needs_review": needs_review,
            }
        )
        if indexes is not UNSET:
            field_dict["indexes"] = indexes
        if created_by is not UNSET:
            field_dict["created_by"] = created_by
        if last_used_at is not UNSET:
            field_dict["last_used_at"] = last_used_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = UUID(d.pop("id"))

        name = d.pop("name")

        description = d.pop("description")

        permissions = []
        _permissions = d.pop("permissions")
        for componentsschemas_agent_permissions_item_data in _permissions:
            componentsschemas_agent_permissions_item = Permission(
                componentsschemas_agent_permissions_item_data
            )

            permissions.append(componentsschemas_agent_permissions_item)

        managers = cast(list[str], d.pop("managers"))

        created_at = datetime.datetime.fromisoformat(d.pop("created_at"))

        disabled = d.pop("disabled")

        needs_review = d.pop("needs_review")

        indexes = cast(list[str], d.pop("indexes", UNSET))

        created_by = d.pop("created_by", UNSET)

        _last_used_at = d.pop("last_used_at", UNSET)
        last_used_at: datetime.datetime | Unset
        if isinstance(_last_used_at, Unset):
            last_used_at = UNSET
        else:
            last_used_at = datetime.datetime.fromisoformat(_last_used_at)

        agent = cls(
            id=id,
            name=name,
            description=description,
            permissions=permissions,
            managers=managers,
            created_at=created_at,
            disabled=disabled,
            needs_review=needs_review,
            indexes=([] if isinstance(indexes, Unset) else indexes),
            created_by=(None if isinstance(created_by, Unset) else created_by),
            last_used_at=(None if isinstance(last_used_at, Unset) else last_used_at),
        )

        agent.additional_properties = d
        return agent

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
