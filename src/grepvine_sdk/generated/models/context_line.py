from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define


T = TypeVar("T", bound="ContextLine")


@_attrs_define
class ContextLine:
    """One line near a result. Text is returned whole up to 64 KiB, and up to 64 KiB away from the result; a line that
    extends past either bound is returned in part and marked truncated.

        Attributes:
            line_number (int):
            text (str):
            text_truncated (bool):
    """

    line_number: int
    text: str
    text_truncated: bool

    def to_dict(self) -> dict[str, Any]:
        line_number = self.line_number

        text = self.text

        text_truncated = self.text_truncated

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "line_number": line_number,
                "text": text,
                "text_truncated": text_truncated,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        line_number = d.pop("line_number")

        text = d.pop("text")

        text_truncated = d.pop("text_truncated")

        context_line = cls(
            line_number=line_number,
            text=text,
            text_truncated=text_truncated,
        )

        return context_line
