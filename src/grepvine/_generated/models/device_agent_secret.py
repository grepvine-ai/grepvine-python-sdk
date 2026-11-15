from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..types import UNSET, Unset

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
        expires_at (datetime.datetime): When the secret stops working, at most one year ahead. Omitted for a secret that
            never expires.
    """

    organization: str
    agent: str
    expires_at: datetime.datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        organization = self.organization
        agent = self.agent
        _expires_at_value = UNSET if self.expires_at is None else self.expires_at
        expires_at: str | Unset = UNSET
        if not isinstance(_expires_at_value, Unset):
            expires_at = _expires_at_value.isoformat()

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "organization": organization,
                "agent": agent,
            }
        )
        if expires_at is not UNSET:
            field_dict["expires_at"] = expires_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        organization = d.pop("organization")

        agent = d.pop("agent")

        _expires_at = d.pop("expires_at", UNSET)
        expires_at: datetime.datetime | Unset
        if isinstance(_expires_at, Unset):
            expires_at = UNSET
        else:
            expires_at = datetime.datetime.fromisoformat(_expires_at)

        device_agent_secret = cls(
            organization=organization,
            agent=agent,
            expires_at=(None if isinstance(expires_at, Unset) else expires_at),
        )

        return device_agent_secret
