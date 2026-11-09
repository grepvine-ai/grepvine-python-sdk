from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define


T = TypeVar("T", bound="InvitationCheckRequest")


@_attrs_define
class InvitationCheckRequest:
    """The invitation to look up.

    Attributes:
        token (str): The token from the invitation link.
    """

    token: str

    def to_dict(self) -> dict[str, Any]:
        token = self.token

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "token": token,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        token = d.pop("token")

        invitation_check_request = cls(
            token=token,
        )

        return invitation_check_request
