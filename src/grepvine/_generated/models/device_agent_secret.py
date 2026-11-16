from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define


from typing import cast
import datetime


T = TypeVar("T", bound="DeviceAgentSecret")


@_attrs_define
class DeviceAgentSecret:
    """A new secret of an agent, which a device asks for instead of an API key.

    Attributes:
        organization (str): A name: of an account, an organization or an agent. Accounts and organizations share one
            namespace; an agent's name is unique within its organization. A name keeps the case it was created with, and any
            spelling that differs only in case refers to it; nothing else in the same namespace can take such a spelling.
        agent (str): A name: of an account, an organization or an agent. Accounts and organizations share one namespace;
            an agent's name is unique within its organization. A name keeps the case it was created with, and any spelling
            that differs only in case refers to it; nothing else in the same namespace can take such a spelling.
        expires_at (datetime.datetime | None): When the secret stops working, at most one year ahead, or null for a
            secret that never expires.
    """

    organization: str
    agent: str
    expires_at: datetime.datetime | None

    def to_dict(self) -> dict[str, Any]:
        organization = self.organization
        agent = self.agent
        expires_at: None | str
        if isinstance(self.expires_at, datetime.datetime):
            expires_at = self.expires_at.isoformat()
        else:
            expires_at = self.expires_at

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "organization": organization,
                "agent": agent,
                "expires_at": expires_at,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        organization = d.pop("organization")

        agent = d.pop("agent")

        def _parse_expires_at(data: object) -> datetime.datetime | None:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                expires_at_type_0 = datetime.datetime.fromisoformat(data)

                return expires_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None, data)

        expires_at = _parse_expires_at(d.pop("expires_at"))

        device_agent_secret = cls(
            organization=organization,
            agent=agent,
            expires_at=expires_at,
        )

        return device_agent_secret
