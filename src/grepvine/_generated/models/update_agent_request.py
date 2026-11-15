from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, TYPE_CHECKING

from attrs import define as _attrs_define

from ..types import UNSET, Unset


if TYPE_CHECKING:
    from ..models.agent_ceiling import AgentCeiling


T = TypeVar("T", bound="UpdateAgentRequest")


@_attrs_define
class UpdateAgentRequest:
    """The changes to make to an agent. A field left out is kept.

    Attributes:
        description (str): What the agent is for, at most 1,024 characters.
        ceiling (AgentCeiling): What an agent reaches and may do, as a whole. Leave indexes out for every index.
        disabled (bool): Disables or enables the agent.
    """

    description: str | None = None
    ceiling: AgentCeiling | None = None
    disabled: bool | None = None

    def to_dict(self) -> dict[str, Any]:
        _description_value = UNSET if self.description is None else self.description
        description = _description_value
        _ceiling_value = UNSET if self.ceiling is None else self.ceiling
        ceiling: dict[str, Any] | Unset = UNSET
        if not isinstance(_ceiling_value, Unset):
            ceiling = _ceiling_value.to_dict()
        _disabled_value = UNSET if self.disabled is None else self.disabled
        disabled = _disabled_value

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if description is not UNSET:
            field_dict["description"] = description
        if ceiling is not UNSET:
            field_dict["ceiling"] = ceiling
        if disabled is not UNSET:
            field_dict["disabled"] = disabled

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.agent_ceiling import AgentCeiling  # noqa: PLC0415

        d = dict(src_dict)
        description = d.pop("description", UNSET)

        _ceiling = d.pop("ceiling", UNSET)
        ceiling: AgentCeiling | Unset
        if isinstance(_ceiling, Unset):
            ceiling = UNSET
        else:
            ceiling = AgentCeiling.from_dict(_ceiling)

        disabled = d.pop("disabled", UNSET)

        update_agent_request = cls(
            description=(None if isinstance(description, Unset) else description),
            ceiling=(None if isinstance(ceiling, Unset) else ceiling),
            disabled=(None if isinstance(disabled, Unset) else disabled),
        )

        return update_agent_request
