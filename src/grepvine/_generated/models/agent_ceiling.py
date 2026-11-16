from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..models.permission import Permission
from typing import cast


T = TypeVar("T", bound="AgentCeiling")


@_attrs_define
class AgentCeiling:
    """What an agent reaches and may do, as a whole. Leave indexes out for every index.

    Attributes:
        permissions (list[Permission]): What an agent may do, each named once: `search`, `read`, `write`, `create_index`
            and `manage_index`, as for a key. `create_index` needs every index.
        indexes (list[str]): The indexes a key reaches, by name, in the key's one organization. Omitted for every index
            of its organizations, including indexes created later. A request names at least one; a key's list is empty once
            every index it named is deleted.
    """

    permissions: list[Permission]
    indexes: list[str] = _attrs_field(factory=list)

    def to_dict(self) -> dict[str, Any]:
        permissions = []
        for componentsschemas_agent_permissions_item_data in self.permissions:
            componentsschemas_agent_permissions_item = (
                componentsschemas_agent_permissions_item_data.value
            )
            permissions.append(componentsschemas_agent_permissions_item)

        _indexes_value = UNSET if not self.indexes else self.indexes
        indexes: list[str] | Unset = UNSET
        if not isinstance(_indexes_value, Unset):
            indexes = _indexes_value

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "permissions": permissions,
            }
        )
        if indexes is not UNSET:
            field_dict["indexes"] = indexes

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        permissions = []
        _permissions = d.pop("permissions")
        for componentsschemas_agent_permissions_item_data in _permissions:
            componentsschemas_agent_permissions_item = Permission(
                componentsschemas_agent_permissions_item_data
            )

            permissions.append(componentsschemas_agent_permissions_item)

        indexes = cast(list[str], d.pop("indexes", UNSET))

        agent_ceiling = cls(
            permissions=permissions,
            indexes=([] if isinstance(indexes, Unset) else indexes),
        )

        return agent_ceiling
