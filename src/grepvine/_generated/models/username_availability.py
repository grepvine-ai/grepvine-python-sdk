from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field


T = TypeVar("T", bound="UsernameAvailability")


@_attrs_define
class UsernameAvailability:
    """Whether a username can be registered.

    Attributes:
        name (str): A name: of an account, an organization or an agent. Accounts and organizations share one namespace;
            an agent's name is unique within its organization. A name keeps the case it was created with, and any spelling
            that differs only in case refers to it; nothing else in the same namespace can take such a spelling.
        available (bool): Whether an account can register this username now.
    """

    name: str
    available: bool
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name
        available = self.available

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
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

        username_availability.additional_properties = d
        return username_availability

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
