from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define


from ..models.add_member_request_role import AddMemberRequestRole


T = TypeVar("T", bound="AddMemberRequest")


@_attrs_define
class AddMemberRequest:
    """
    Attributes:
        user (str): An account or organization name. Accounts and organizations share one namespace. A name keeps the
            case it was created with, and any spelling that differs only in case refers to it; no other account or
            organization can take such a spelling.
        role (AddMemberRequestRole):
    """

    user: str
    role: AddMemberRequestRole

    def to_dict(self) -> dict[str, Any]:
        user = self.user

        role = self.role.value

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "user": user,
                "role": role,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        user = d.pop("user")

        role = AddMemberRequestRole(d.pop("role"))

        add_member_request = cls(
            user=user,
            role=role,
        )

        return add_member_request
