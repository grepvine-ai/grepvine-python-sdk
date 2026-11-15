from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..types import UNSET, Unset


T = TypeVar("T", bound="UpdateOrganizationRequest")


@_attrs_define
class UpdateOrganizationRequest:
    """The settings to change. A field left out is kept.

    Attributes:
        members_create_agents (bool): Whether developers can create agents.
    """

    members_create_agents: bool | None = None

    def to_dict(self) -> dict[str, Any]:
        _members_create_agents_value = (
            UNSET if self.members_create_agents is None else self.members_create_agents
        )
        members_create_agents = _members_create_agents_value

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if members_create_agents is not UNSET:
            field_dict["members_create_agents"] = members_create_agents

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        members_create_agents = d.pop("members_create_agents", UNSET)

        update_organization_request = cls(
            members_create_agents=(
                None if isinstance(members_create_agents, Unset) else members_create_agents
            ),
        )

        return update_organization_request
