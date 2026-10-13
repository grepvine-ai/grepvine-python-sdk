from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define


T = TypeVar("T", bound="DeviceAuthorizationRequest")


@_attrs_define
class DeviceAuthorizationRequest:
    """
    Attributes:
        api_key_name (str):
    """

    api_key_name: str

    def to_dict(self) -> dict[str, Any]:
        api_key_name = self.api_key_name

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "api_key_name": api_key_name,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        api_key_name = d.pop("api_key_name")

        device_authorization_request = cls(
            api_key_name=api_key_name,
        )

        return device_authorization_request
