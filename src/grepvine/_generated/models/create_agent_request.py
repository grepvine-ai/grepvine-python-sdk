from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..models.permission import Permission
from typing import cast


T = TypeVar("T", bound="CreateAgentRequest")


@_attrs_define
class CreateAgentRequest:
    """A new agent. Leave indexes out for every index of the organization, including indexes created later.

    Attributes:
        name (str): A name: of an account, an organization or an agent. Accounts and organizations share one namespace;
            an agent's name is unique within its organization. A name keeps the case it was created with, and any spelling
            that differs only in case refers to it; nothing else in the same namespace can take such a spelling.
        permissions (list[Permission]): What an agent may do, each named once: `search`, `read`, `write`, `create_index`
            and `manage_index`, as for a key. `create_index` needs every index.
        description (str): What the agent is for, at most 1,024 characters.
        indexes (list[str]): The indexes a key reaches, by name, in the key's one organization. Omitted for every index
            of its organizations, including indexes created later. A request names at least one; a key's list is empty once
            every index it named is deleted.
    """

    name: str
    permissions: list[Permission]
    description: str | None = None
    indexes: list[str] = _attrs_field(factory=list)

    def to_dict(self) -> dict[str, Any]:
        name = self.name
        permissions = []
        for componentsschemas_agent_permissions_item_data in self.permissions:
            componentsschemas_agent_permissions_item = (
                componentsschemas_agent_permissions_item_data.value
            )
            permissions.append(componentsschemas_agent_permissions_item)

        _description_value = UNSET if self.description is None else self.description
        description = _description_value
        _indexes_value = UNSET if self.indexes is None else self.indexes
        indexes: list[str] | Unset = UNSET
        if not isinstance(_indexes_value, Unset):
            indexes = _indexes_value

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "name": name,
                "permissions": permissions,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description
        if indexes is not UNSET:
            field_dict["indexes"] = indexes

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name")

        permissions = []
        _permissions = d.pop("permissions")
        for componentsschemas_agent_permissions_item_data in _permissions:
            componentsschemas_agent_permissions_item = Permission(
                componentsschemas_agent_permissions_item_data
            )

            permissions.append(componentsschemas_agent_permissions_item)

        description = d.pop("description", UNSET)

        indexes = cast(list[str], d.pop("indexes", UNSET))

        create_agent_request = cls(
            name=name,
            permissions=permissions,
            description=(None if isinstance(description, Unset) else description),
            indexes=([] if isinstance(indexes, Unset) else indexes),
        )

        return create_agent_request
