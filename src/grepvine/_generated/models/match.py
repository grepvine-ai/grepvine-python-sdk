from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define


T = TypeVar("T", bound="Match")


@_attrs_define
class Match:
    """One match, as a byte range of the document.

    Attributes:
        offset (int): Byte offset of the match within the document. It starts at byte `offset - text_start_offset` of
            the result's text.
        length (int): The match's length in bytes.
    """

    offset: int
    length: int

    def to_dict(self) -> dict[str, Any]:
        offset = self.offset
        length = self.length

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "offset": offset,
                "length": length,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        offset = d.pop("offset")

        length = d.pop("length")

        match = cls(
            offset=offset,
            length=length,
        )

        return match
