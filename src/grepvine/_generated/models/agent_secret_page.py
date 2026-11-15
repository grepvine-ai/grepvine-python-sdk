from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, TYPE_CHECKING

from attrs import define as _attrs_define


if TYPE_CHECKING:
    from ..models.agent_secret import AgentSecret


T = TypeVar("T", bound="AgentSecretPage")


@_attrs_define
class AgentSecretPage:
    """An agent's active secrets.

    Attributes:
        secrets (list[AgentSecret]):
    """

    secrets: list[AgentSecret]

    def to_dict(self) -> dict[str, Any]:
        secrets = []
        for secrets_item_data in self.secrets:
            secrets_item = secrets_item_data.to_dict()
            secrets.append(secrets_item)

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "secrets": secrets,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.agent_secret import AgentSecret  # noqa: PLC0415

        d = dict(src_dict)
        secrets = []
        _secrets = d.pop("secrets")
        for secrets_item_data in _secrets:
            secrets_item = AgentSecret.from_dict(secrets_item_data)

            secrets.append(secrets_item)

        agent_secret_page = cls(
            secrets=secrets,
        )

        return agent_secret_page
