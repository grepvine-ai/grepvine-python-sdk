from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field


T = TypeVar("T", bound="ContextLine")


@_attrs_define
class ContextLine:
    """One line near a result. Text is returned whole up to 64 KiB, and up to 64 KiB away from the result; a line that
    extends past either bound is returned in part and marked truncated.

        Attributes:
            line_number (int): One-based number of the line.
            text (str): The line's text, without its line break, up to 64 KiB.
            text_truncated (bool): Whether the line was cut.
    """

    line_number: int
    text: str
    text_truncated: bool
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        line_number = self.line_number
        text = self.text
        text_truncated = self.text_truncated

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
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

        context_line.additional_properties = d
        return context_line

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
