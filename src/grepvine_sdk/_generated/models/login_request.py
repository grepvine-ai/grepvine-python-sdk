from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define


T = TypeVar("T", bound="LoginRequest")


@_attrs_define
class LoginRequest:
    """
    Attributes:
        identifier (str): A username or an email address, matched case-insensitively.
        password (str):
    """

    identifier: str
    password: str

    def to_dict(self) -> dict[str, Any]:
        identifier = self.identifier

        password = self.password

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "identifier": identifier,
                "password": password,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        identifier = d.pop("identifier")

        password = d.pop("password")

        login_request = cls(
            identifier=identifier,
            password=password,
        )

        return login_request
