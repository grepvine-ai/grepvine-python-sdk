from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, TYPE_CHECKING

from attrs import define as _attrs_define


if TYPE_CHECKING:
    from ..models.agent import Agent


T = TypeVar("T", bound="AgentPage")


@_attrs_define
class AgentPage:
    """An organization's agents.

    Attributes:
        agents (list[Agent]):
    """

    agents: list[Agent]

    def to_dict(self) -> dict[str, Any]:
        agents = []
        for agents_item_data in self.agents:
            agents_item = agents_item_data.to_dict()
            agents.append(agents_item)

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "agents": agents,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.agent import Agent  # noqa: PLC0415

        d = dict(src_dict)
        agents = []
        _agents = d.pop("agents")
        for agents_item_data in _agents:
            agents_item = Agent.from_dict(agents_item_data)

            agents.append(agents_item)

        agent_page = cls(
            agents=agents,
        )

        return agent_page
