from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define


T = TypeVar("T", bound="DeviceAuthorization")


@_attrs_define
class DeviceAuthorization:
    """
    Attributes:
        device_code (str):
        user_code (str):
        verification_uri (str):
        verification_uri_complete (str):
        expires_in (int):
        interval (int):
    """

    device_code: str
    user_code: str
    verification_uri: str
    verification_uri_complete: str
    expires_in: int
    interval: int

    def to_dict(self) -> dict[str, Any]:
        device_code = self.device_code

        user_code = self.user_code

        verification_uri = self.verification_uri

        verification_uri_complete = self.verification_uri_complete

        expires_in = self.expires_in

        interval = self.interval

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "device_code": device_code,
                "user_code": user_code,
                "verification_uri": verification_uri,
                "verification_uri_complete": verification_uri_complete,
                "expires_in": expires_in,
                "interval": interval,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        device_code = d.pop("device_code")

        user_code = d.pop("user_code")

        verification_uri = d.pop("verification_uri")

        verification_uri_complete = d.pop("verification_uri_complete")

        expires_in = d.pop("expires_in")

        interval = d.pop("interval")

        device_authorization = cls(
            device_code=device_code,
            user_code=user_code,
            verification_uri=verification_uri,
            verification_uri_complete=verification_uri_complete,
            expires_in=expires_in,
            interval=interval,
        )

        return device_authorization
