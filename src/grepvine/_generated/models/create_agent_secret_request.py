from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..types import UNSET, Unset

import datetime


T = TypeVar("T", bound="CreateAgentSecretRequest")


@_attrs_define
class CreateAgentSecretRequest:
    """A new agent secret.

    Attributes:
        expires_at (datetime.datetime): When the secret stops working, at most one year ahead. Omitted for a secret that
            never expires.
    """

    expires_at: datetime.datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        _expires_at_value = UNSET if self.expires_at is None else self.expires_at
        expires_at: str | Unset = UNSET
        if not isinstance(_expires_at_value, Unset):
            expires_at = _expires_at_value.isoformat()

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if expires_at is not UNSET:
            field_dict["expires_at"] = expires_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        _expires_at = d.pop("expires_at", UNSET)
        expires_at: datetime.datetime | Unset
        if isinstance(_expires_at, Unset):
            expires_at = UNSET
        else:
            expires_at = datetime.datetime.fromisoformat(_expires_at)

        create_agent_secret_request = cls(
            expires_at=(None if isinstance(expires_at, Unset) else expires_at),
        )

        return create_agent_secret_request
