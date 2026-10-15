from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define


T = TypeVar("T", bound="TransferOwnershipRequest")


@_attrs_define
class TransferOwnershipRequest:
    """
    Attributes:
        user (str): An account or organization name. Accounts and organizations share one namespace. A name keeps the
            case it was created with, and any spelling that differs only in case refers to it; no other account or
            organization can take such a spelling.
    """

    user: str

    def to_dict(self) -> dict[str, Any]:
        user = self.user

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "user": user,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        user = d.pop("user")

        transfer_ownership_request = cls(
            user=user,
        )

        return transfer_ownership_request
