from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..types import UNSET, Unset

from ..models.query_request_mode import QueryRequestMode


T = TypeVar("T", bound="QueryRequest")


@_attrs_define
class QueryRequest:
    """
    Attributes:
        pattern (str):
        mode (QueryRequestMode | Unset):  Default: QueryRequestMode.REGEX.
        case_sensitive (bool | Unset):  Default: True.
        whole_word (bool | Unset):  Default: False.
        multiline (bool | Unset): Let a match span lines. Without it a pattern matches within one line, `^` and `$` mark
            the line's edges, and a character class never matches a line break; a pattern that contains a line break is
            rejected. With it the pattern is matched against the whole document, `^` and `$` still mark line edges, `\\A`
            and `\\z` mark the document's edges, and a match may contain line breaks. Default: False.
        filter_ (str | Unset):
        lines_before (int | Unset): How many lines before each result to return with it, from the same document.
            Default: 0.
        lines_after (int | Unset): How many lines after each result to return with it, from the same document. Default:
            0.
    """

    pattern: str
    mode: QueryRequestMode | Unset = QueryRequestMode.REGEX
    case_sensitive: bool | Unset = True
    whole_word: bool | Unset = False
    multiline: bool | Unset = False
    filter_: str | Unset = UNSET
    lines_before: int | Unset = 0
    lines_after: int | Unset = 0

    def to_dict(self) -> dict[str, Any]:
        pattern = self.pattern

        mode: str | Unset = UNSET
        if not isinstance(self.mode, Unset):
            mode = self.mode.value

        case_sensitive = self.case_sensitive

        whole_word = self.whole_word

        multiline = self.multiline

        filter_ = self.filter_

        lines_before = self.lines_before

        lines_after = self.lines_after

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "pattern": pattern,
            }
        )
        if mode is not UNSET:
            field_dict["mode"] = mode
        if case_sensitive is not UNSET:
            field_dict["case_sensitive"] = case_sensitive
        if whole_word is not UNSET:
            field_dict["whole_word"] = whole_word
        if multiline is not UNSET:
            field_dict["multiline"] = multiline
        if filter_ is not UNSET:
            field_dict["filter"] = filter_
        if lines_before is not UNSET:
            field_dict["lines_before"] = lines_before
        if lines_after is not UNSET:
            field_dict["lines_after"] = lines_after

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        pattern = d.pop("pattern")

        _mode = d.pop("mode", UNSET)
        mode: QueryRequestMode | Unset
        if isinstance(_mode, Unset):
            mode = UNSET
        else:
            mode = QueryRequestMode(_mode)

        case_sensitive = d.pop("case_sensitive", UNSET)

        whole_word = d.pop("whole_word", UNSET)

        multiline = d.pop("multiline", UNSET)

        filter_ = d.pop("filter", UNSET)

        lines_before = d.pop("lines_before", UNSET)

        lines_after = d.pop("lines_after", UNSET)

        query_request = cls(
            pattern=pattern,
            mode=mode,
            case_sensitive=case_sensitive,
            whole_word=whole_word,
            multiline=multiline,
            filter_=filter_,
            lines_before=lines_before,
            lines_after=lines_after,
        )

        return query_request
