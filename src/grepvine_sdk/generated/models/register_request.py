from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define


T = TypeVar("T", bound="RegisterRequest")


@_attrs_define
class RegisterRequest:
    """
    Attributes:
        name (str): An account or organization name. Accounts and organizations share one namespace. A name keeps the
            case it was created with, and any spelling that differs only in case refers to it; no other account or
            organization can take such a spelling.
        email (str):
        password (str):
    """

    name: str
    email: str
    password: str

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        email = self.email

        password = self.password

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "name": name,
                "email": email,
                "password": password,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name")

        email = d.pop("email")

        password = d.pop("password")

        register_request = cls(
            name=name,
            email=email,
            password=password,
        )

        return register_request
