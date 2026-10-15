"""Request validation and request bodies for the API operations."""

from __future__ import annotations

import unicodedata
from collections.abc import Mapping, Sequence
from typing import Final

from grepvine_sdk._generated.models import QueryRequest, QueryRequestMode
from grepvine_sdk._generated.types import UNSET

MIN_IDEMPOTENCY_KEY_LENGTH: Final = 16
MAX_IDEMPOTENCY_KEY_LENGTH: Final = 128
MAX_CONTEXT_LINES: Final = 20
MAX_DESCRIPTION_LENGTH: Final = 16384
MAX_TAGS: Final = 64
MAX_TAG_KEY_LENGTH: Final = 128
MAX_TAG_VALUE_LENGTH: Final = 1024


def idempotency_key(key: str) -> str:
    if not MIN_IDEMPOTENCY_KEY_LENGTH <= len(key) <= MAX_IDEMPOTENCY_KEY_LENGTH:
        raise ValueError(
            f"idempotency_key must be {MIN_IDEMPOTENCY_KEY_LENGTH} to "
            f"{MAX_IDEMPOTENCY_KEY_LENGTH} characters"
        )
    return key


def check_preconditions(if_match: str | None, if_none_match: bool) -> None:
    if if_match is not None and if_none_match:
        raise ValueError("if_match and if_none_match cannot be combined")
    if if_match is not None and not if_match:
        raise ValueError("if_match must be a revision")


def range_header(byte_range: tuple[int | None, int | None]) -> str:
    start, end = byte_range
    if start is None and end is None:
        raise ValueError("range needs a start, an end, or both")
    if start is not None and start < 0:
        raise ValueError("range start must not be negative")
    if end is not None and end < 0:
        raise ValueError("range end must not be negative")
    if start is None:
        return f"bytes=-{end}"
    if end is None:
        return f"bytes={start}-"
    if end < start:
        raise ValueError("range end must not precede its start")
    return f"bytes={start}-{end}"


def index_description(description: str) -> str:
    if not isinstance(description, str):
        raise TypeError("description must be a string")
    if len(description) > MAX_DESCRIPTION_LENGTH:
        raise ValueError(f"description must be at most {MAX_DESCRIPTION_LENGTH} characters")
    return description


def _has_control_characters(text: str) -> bool:
    return any(unicodedata.category(char) == "Cc" for char in text)


def _tag_key(key: object) -> str:
    if not isinstance(key, str):
        raise TypeError("tag keys must be strings")
    if not 1 <= len(key) <= MAX_TAG_KEY_LENGTH:
        raise ValueError(f"tag keys must be 1 to {MAX_TAG_KEY_LENGTH} characters")
    if any(char.isspace() for char in key) or _has_control_characters(key):
        raise ValueError(f"tag key {key!r} must not contain whitespace or control characters")
    return key


def _tag_value(key: str, value: object) -> str:
    if not isinstance(value, str):
        raise TypeError(f"the value of tag {key!r} must be a string")
    if len(value) > MAX_TAG_VALUE_LENGTH:
        raise ValueError(
            f"the value of tag {key!r} must be at most {MAX_TAG_VALUE_LENGTH} characters"
        )
    if _has_control_characters(value):
        raise ValueError(f"the value of tag {key!r} must not contain control characters")
    return value


def index_tags(tags: Mapping[str, str]) -> dict[str, str]:
    """Check the tags of a new index: every key names a string value."""
    if not isinstance(tags, Mapping):
        raise TypeError("tags must be a mapping of strings to strings")
    if len(tags) > MAX_TAGS:
        raise ValueError(f"an index has at most {MAX_TAGS} tags")
    return {_tag_key(key): _tag_value(key, value) for key, value in tags.items()}


def tag_changes(changes: Mapping[str, str | None]) -> dict[str, str | None]:
    """Check a tag update: a string value sets the key and ``None`` removes it."""
    if not isinstance(changes, Mapping):
        raise TypeError("tags must be a mapping of strings to strings or None")
    if len(changes) > MAX_TAGS:
        raise ValueError(f"an update changes at most {MAX_TAGS} tags")
    return {
        _tag_key(key): None if value is None else _tag_value(key, value)
        for key, value in changes.items()
    }


def query_request(
    pattern: str,
    *,
    regex: bool = True,
    case_sensitive: bool = True,
    whole_word: bool = False,
    multiline: bool = False,
    filter: str | None = None,
    lines_before: int = 0,
    lines_after: int = 0,
) -> QueryRequest:
    """A search request body. Only non-default fields are sent, always the same way."""
    if not pattern:
        raise ValueError("pattern must not be empty")
    if whole_word and regex:
        raise ValueError("whole_word requires regex=False")
    if not 0 <= lines_before <= MAX_CONTEXT_LINES or not 0 <= lines_after <= MAX_CONTEXT_LINES:
        raise ValueError(f"lines_before and lines_after must be between 0 and {MAX_CONTEXT_LINES}")
    return QueryRequest(
        pattern=pattern,
        mode=UNSET if regex else QueryRequestMode.LITERAL,
        case_sensitive=UNSET if case_sensitive else False,
        whole_word=True if whole_word else UNSET,
        multiline=True if multiline else UNSET,
        filter_=filter or UNSET,
        lines_before=lines_before or UNSET,
        lines_after=lines_after or UNSET,
    )


def combine_filters(
    filter: str | None,
    filters: Sequence[str] | None,
) -> str | None:
    """Join several filter expressions with AND, or pass a single one through."""
    if filter is not None and filters is not None:
        raise ValueError("pass either filter or filters, not both")
    if filter is not None:
        return filter or None
    if not filters:
        return None
    if any(not expression for expression in filters):
        raise ValueError("filters must not contain empty expressions")
    if len(filters) == 1:
        return filters[0]
    return " AND ".join(f"({expression})" for expression in filters)
