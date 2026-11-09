from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..types import UNSET, Unset

from ..models.query_request_mode import QueryRequestMode


T = TypeVar("T", bound="QueryRequest")


@_attrs_define
class QueryRequest:
    """A search: the pattern, how to match it, which documents to search and how much context to return.

    Attributes:
        pattern (str): What to search for: an RE2 regular expression, or literal text when `mode` is `literal`.
            Required; at most 8,192 characters of valid UTF-8.
        mode (QueryRequestMode): How to read the pattern: `regex` (the default) for RE2 syntax, without backreferences
            or lookaround, or `literal` to match its bytes exactly, with no escaping needed. Default:
            QueryRequestMode.REGEX.
        case_sensitive (bool): Whether case must match. Defaults to true. False matches under Unicode simple case
            folding; in a regex, `(?i)` does the same for part of the pattern. Default: True.
        whole_word (bool): Match only where the characters on either side of the match aren't word characters: letters,
            digits or `_`. Defaults to false. Valid only in literal mode. Default: False.
        multiline (bool): Let a match span lines. Without it a pattern matches within one line, `^` and `$` mark the
            line's edges, and a character class never matches a line break; a pattern that contains a line break is
            rejected. With it the pattern is matched against the whole document, `^` and `$` still mark line edges, `\\A`
            and `\\z` mark the document's edges, and a match may contain line breaks. Default: False.
        filter_ (str): Search only the documents whose metadata matches this expression, such as `path STARTSWITH 'src/'
            AND size < 1048576`. At most 8,192 characters. Omit it to search every document.
        lines_before (int): How many lines before each result to return with it, from the same document. Default: 0.
        lines_after (int): How many lines after each result to return with it, from the same document. Default: 0.
    """

    pattern: str
    mode: QueryRequestMode = QueryRequestMode.REGEX
    case_sensitive: bool = True
    whole_word: bool = False
    multiline: bool = False
    filter_: str | None = None
    lines_before: int = 0
    lines_after: int = 0

    def to_dict(self) -> dict[str, Any]:
        pattern = self.pattern
        _mode_value = UNSET if self.mode is None else self.mode
        mode: str | Unset = UNSET
        if not isinstance(_mode_value, Unset):
            mode = _mode_value.value

        _case_sensitive_value = UNSET if self.case_sensitive is None else self.case_sensitive
        case_sensitive = _case_sensitive_value
        _whole_word_value = UNSET if self.whole_word is None else self.whole_word
        whole_word = _whole_word_value
        _multiline_value = UNSET if self.multiline is None else self.multiline
        multiline = _multiline_value
        _filter__value = UNSET if self.filter_ is None else self.filter_
        filter_ = _filter__value
        _lines_before_value = UNSET if self.lines_before is None else self.lines_before
        lines_before = _lines_before_value
        _lines_after_value = UNSET if self.lines_after is None else self.lines_after
        lines_after = _lines_after_value

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
            mode=(QueryRequestMode.REGEX if isinstance(mode, Unset) else mode),
            case_sensitive=(True if isinstance(case_sensitive, Unset) else case_sensitive),
            whole_word=(False if isinstance(whole_word, Unset) else whole_word),
            multiline=(False if isinstance(multiline, Unset) else multiline),
            filter_=(None if isinstance(filter_, Unset) else filter_),
            lines_before=(0 if isinstance(lines_before, Unset) else lines_before),
            lines_after=(0 if isinstance(lines_after, Unset) else lines_after),
        )

        return query_request
