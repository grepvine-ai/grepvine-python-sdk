from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define


T = TypeVar("T", bound="UsernameAvailability")


@_attrs_define
class UsernameAvailability:
    """
    Attributes:
        name (str): An account or organization name. Accounts and organizations share one namespace. A name keeps the
            case it was created with, and any spelling that differs only in case refers to it; no other account or
            organization can take such a spelling.
        available (bool):
    """

    name: str
    available: bool

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        available = self.available

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "name": name,
                "available": available,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name")

        available = d.pop("available")

        username_availability = cls(
            name=name,
            available=available,
        )

        return username_availability
