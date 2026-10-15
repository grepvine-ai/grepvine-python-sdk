from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define


T = TypeVar("T", bound="DeviceDecisionRequest")


@_attrs_define
class DeviceDecisionRequest:
    """
    Attributes:
        user_code (str):
    """

    user_code: str

    def to_dict(self) -> dict[str, Any]:
        user_code = self.user_code

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "user_code": user_code,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        user_code = d.pop("user_code")

        device_decision_request = cls(
            user_code=user_code,
        )

        return device_decision_request
