from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define


T = TypeVar("T", bound="Pagination")


@_attrs_define
class Pagination:
    """A page may hold fewer results than the requested amount, possibly none, while has_next is true; a query page stops
    at the server's soft time budget and next_page_id resumes exactly after the last candidate it examined. Clients
    continue while has_next is true.

        Attributes:
            next_page_id (str):
            has_next (bool):
    """

    next_page_id: str
    has_next: bool

    def to_dict(self) -> dict[str, Any]:
        next_page_id = self.next_page_id

        has_next = self.has_next

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "next_page_id": next_page_id,
                "has_next": has_next,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        next_page_id = d.pop("next_page_id")

        has_next = d.pop("has_next")

        pagination = cls(
            next_page_id=next_page_id,
            has_next=has_next,
        )

        return pagination
