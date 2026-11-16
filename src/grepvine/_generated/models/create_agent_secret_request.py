from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define


from typing import cast
import datetime


T = TypeVar("T", bound="CreateAgentSecretRequest")


@_attrs_define
class CreateAgentSecretRequest:
    """A new agent secret.

    Attributes:
        expires_at (datetime.datetime | None): When the secret stops working, at most one year ahead, or null for a
            secret that never expires.
    """

    expires_at: datetime.datetime | None

    def to_dict(self) -> dict[str, Any]:
        expires_at: None | str
        if isinstance(self.expires_at, datetime.datetime):
            expires_at = self.expires_at.isoformat()
        else:
            expires_at = self.expires_at

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "expires_at": expires_at,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

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

        create_agent_secret_request = cls(
            expires_at=expires_at,
        )

        return create_agent_secret_request
