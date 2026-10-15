from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, TYPE_CHECKING

from attrs import define as _attrs_define

from ..types import UNSET, Unset


if TYPE_CHECKING:
    from ..models.context_line import ContextLine
    from ..models.match import Match


T = TypeVar("T", bound="QueryResult")


@_attrs_define
class QueryResult:
    """One match, or several matches that share lines, together with the lines it covers. A result covers one line unless
    the query set multiline and a match spans lines.

        Attributes:
            key (str):
            revision (str):
            line_number (int): One-based number of the first line the result covers.
            last_line_number (int): One-based number of the last line the result covers. Equal to line_number unless a match
                spans lines.
            line_start_offset (int): Byte offset of the first covered line's start within the document.
            line_end_offset (int): Byte offset just past the last covered line, excluding its line break.
            text_start_offset (int): Byte offset of the first byte of text within the document.
            text_line_number (int): One-based number of the line text begins on. Equal to line_number unless text was cut at
                its start.
            text (str): The covered lines, up to 64 KiB, centered on the first match when they are longer. Line breaks
                between covered lines are kept; the last line's break is not.
            matches (list[Match]): Every match on the covered lines that lies at least partly within text, with byte offsets
                and lengths relative to the document. A match that consumed the last line's break extends one byte past text.
            text_truncated (bool): Whether text was cut at either end.
            matches_truncated (bool): Whether matches were left out, because there were more than 4096 or because they lie
                outside text.
            lines_before (list[ContextLine] | Unset): The requested lines before the result, in document order, ending at
                the line just above its first line. Fewer are returned at the start of the document, and the field is omitted
                when there are none.
            lines_after (list[ContextLine] | Unset): The requested lines after the result, in document order, starting at
                the line just below its last line. Fewer are returned at the end of the document, and the field is omitted when
                there are none.
    """

    key: str
    revision: str
    line_number: int
    last_line_number: int
    line_start_offset: int
    line_end_offset: int
    text_start_offset: int
    text_line_number: int
    text: str
    matches: list[Match]
    text_truncated: bool
    matches_truncated: bool
    lines_before: list[ContextLine] | Unset = UNSET
    lines_after: list[ContextLine] | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        key = self.key

        revision = self.revision

        line_number = self.line_number

        last_line_number = self.last_line_number

        line_start_offset = self.line_start_offset

        line_end_offset = self.line_end_offset

        text_start_offset = self.text_start_offset

        text_line_number = self.text_line_number

        text = self.text

        matches = []
        for matches_item_data in self.matches:
            matches_item = matches_item_data.to_dict()
            matches.append(matches_item)

        text_truncated = self.text_truncated

        matches_truncated = self.matches_truncated

        lines_before: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.lines_before, Unset):
            lines_before = []
            for lines_before_item_data in self.lines_before:
                lines_before_item = lines_before_item_data.to_dict()
                lines_before.append(lines_before_item)

        lines_after: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.lines_after, Unset):
            lines_after = []
            for lines_after_item_data in self.lines_after:
                lines_after_item = lines_after_item_data.to_dict()
                lines_after.append(lines_after_item)

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "key": key,
                "revision": revision,
                "line_number": line_number,
                "last_line_number": last_line_number,
                "line_start_offset": line_start_offset,
                "line_end_offset": line_end_offset,
                "text_start_offset": text_start_offset,
                "text_line_number": text_line_number,
                "text": text,
                "matches": matches,
                "text_truncated": text_truncated,
                "matches_truncated": matches_truncated,
            }
        )
        if lines_before is not UNSET:
            field_dict["lines_before"] = lines_before
        if lines_after is not UNSET:
            field_dict["lines_after"] = lines_after

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.context_line import ContextLine  # noqa: PLC0415
        from ..models.match import Match  # noqa: PLC0415

        d = dict(src_dict)
        key = d.pop("key")

        revision = d.pop("revision")

        line_number = d.pop("line_number")

        last_line_number = d.pop("last_line_number")

        line_start_offset = d.pop("line_start_offset")

        line_end_offset = d.pop("line_end_offset")

        text_start_offset = d.pop("text_start_offset")

        text_line_number = d.pop("text_line_number")

        text = d.pop("text")

        matches = []
        _matches = d.pop("matches")
        for matches_item_data in _matches:
            matches_item = Match.from_dict(matches_item_data)

            matches.append(matches_item)

        text_truncated = d.pop("text_truncated")

        matches_truncated = d.pop("matches_truncated")

        _lines_before = d.pop("lines_before", UNSET)
        lines_before: list[ContextLine] | Unset = UNSET
        if _lines_before is not UNSET:
            lines_before = []
            for lines_before_item_data in _lines_before:
                lines_before_item = ContextLine.from_dict(lines_before_item_data)

                lines_before.append(lines_before_item)

        _lines_after = d.pop("lines_after", UNSET)
        lines_after: list[ContextLine] | Unset = UNSET
        if _lines_after is not UNSET:
            lines_after = []
            for lines_after_item_data in _lines_after:
                lines_after_item = ContextLine.from_dict(lines_after_item_data)

                lines_after.append(lines_after_item)

        query_result = cls(
            key=key,
            revision=revision,
            line_number=line_number,
            last_line_number=last_line_number,
            line_start_offset=line_start_offset,
            line_end_offset=line_end_offset,
            text_start_offset=text_start_offset,
            text_line_number=text_line_number,
            text=text,
            matches=matches,
            text_truncated=text_truncated,
            matches_truncated=matches_truncated,
            lines_before=lines_before,
            lines_after=lines_after,
        )

        return query_result
