from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define


from ..models.update_member_request_role import UpdateMemberRequestRole


T = TypeVar("T", bound="UpdateMemberRequest")


@_attrs_define
class UpdateMemberRequest:
    """
    Attributes:
        role (UpdateMemberRequestRole):
    """

    role: UpdateMemberRequestRole

    def to_dict(self) -> dict[str, Any]:
        role = self.role.value

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "role": role,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        role = UpdateMemberRequestRole(d.pop("role"))

        update_member_request = cls(
            role=role,
        )

        return update_member_request
