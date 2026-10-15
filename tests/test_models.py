from __future__ import annotations

from datetime import UTC, datetime

import httpx

from grepvine_sdk import (
    Document,
    DocumentError,
    IndexData,
    Match,
    MutationResult,
    SearchResult,
    Span,
)
from grepvine_sdk._core import parse
from grepvine_sdk.models import ContentRange


def _result(text: str, matches: list[tuple[int, int]], text_start: int = 100) -> SearchResult:
    return SearchResult(
        key="k",
        revision="r",
        line_number=1,
        last_line_number=1,
        line_start_offset=text_start,
        line_end_offset=text_start + len(text.encode()),
        text_start_offset=text_start,
        text_line_number=1,
        text=text,
        matches=tuple(Match(offset=text_start + o, length=n) for o, n in matches),
        text_truncated=False,
        matches_truncated=False,
    )


def test_match_spans_handle_multibyte_text() -> None:
    result = _result("héllo wörld", [(1, 3), (7, 3)])
    assert result.text_bytes == "héllo wörld".encode()
    assert result.match_byte_spans() == [Span(1, 4), Span(7, 10)]
    assert result.match_spans() == [Span(1, 3), Span(6, 8)]
    assert result.match_texts() == ["él", "wö"]
    assert result.matches[0].end == 104


def test_match_past_the_text_is_clipped() -> None:
    result = _result("abc", [(2, 2)])
    assert result.match_byte_spans() == [Span(2, 3)]
    assert result.match_texts() == ["c"]
    before = _result("abc", [(-2, 3)])
    assert before.match_byte_spans() == [Span(0, 1)]


def test_lines_helpers() -> None:
    result = SearchResult._from_json(
        {
            "key": "k",
            "revision": "r",
            "line_number": 4,
            "last_line_number": 5,
            "line_start_offset": 0,
            "line_end_offset": 7,
            "text_start_offset": 0,
            "text_line_number": 4,
            "text": "one\ntwo",
            "matches": [],
            "text_truncated": True,
            "matches_truncated": False,
            "extra_field": "ignored",
        }
    )
    assert result.lines == ["one", "two"]
    assert result.numbered_lines() == [(4, "one"), (5, "two")]
    assert result.lines_before == ()
    assert result.lines_after == ()
    assert result.text_truncated is True


_INDEX_JSON = {
    "id": "i",
    "organization": "acme",
    "name": "docs",
    "canonical_id": "i",
    "state": "ready",
    "document_count": 2,
    "content_bytes": 9,
    "created_at": "2026-09-06T00:00:00Z",
    "last_updated_at": "2026-09-06T01:00:00Z",
    "optimization_progress_percent": 40,
}


def test_index_data_and_document() -> None:
    data = IndexData._from_json(_INDEX_JSON)
    assert data.ref == "acme/docs"
    assert data.last_updated_at == datetime(2026, 9, 6, 1, tzinfo=UTC)
    assert data.optimization_progress_percent == 40
    assert data.description == ""
    assert data.tags == {}
    assert hash(data) == hash(IndexData._from_json({**_INDEX_JSON, "tags": {"team": "search"}}))
    tagged = IndexData._from_json({**_INDEX_JSON, "tags": {"team": "search"}})
    assert tagged.tags == {"team": "search"}
    assert tagged != data

    document = Document(key="k", revision="r", content=b"abc", metadata={})
    assert document.size == 3
    assert bytes(document) == b"abc"
    assert document.text() == "abc"
    ranged = Document(
        key="k", revision="r", content=b"b", metadata={}, content_range=ContentRange(1, 1, 3)
    )
    assert ranged.size == 3


def test_parse_helpers() -> None:
    assert parse.revision_from_etag(None) == ""
    assert parse.revision_from_etag('"abc"') == "abc"
    assert parse.revision_from_etag('W/"abc"') == "abc"
    assert parse.revision_from_etag(" abc ") == "abc"
    assert parse.content_range("bytes 0-4/10") == ContentRange(0, 4, 10)
    assert parse.content_range("bytes 0-4/*") == ContentRange(0, 4, 5)
    assert parse.content_range("nonsense") is None
    assert parse.content_range(None) is None

    response = httpx.Response(
        200, headers={"etag": "r", "x-grepvine-metadata": "not json"}, content=b"x"
    )
    assert parse.document(response, "k").metadata == {}
    response = httpx.Response(
        206, headers={"etag": "r", "content-range": "bytes 1-1/3"}, content=b"x"
    )
    assert parse.document(response, "k").content_range == ContentRange(1, 1, 3)


def test_mutation_results_carry_revisions_or_errors() -> None:
    stored = MutationResult._from_json({"key": "a", "revision": "r1", "extra_field": 1})
    assert (stored.key, stored.revision, stored.error, stored.ok) == ("a", "r1", None, True)

    missing = MutationResult._from_json(
        {"key": "b", "error": {"code": "not_found", "reason": "resource", "error": "gone"}}
    )
    assert (missing.revision, missing.ok) == (None, False)
    assert missing.error == DocumentError(code="not_found", reason="resource", message="gone")
    assert str(missing.error) == "gone (not_found)"

    sparse = MutationResult._from_json({"key": "c", "error": {}})
    assert sparse.error is not None
    assert (sparse.error.code, sparse.error.reason) == ("request_failed", "")
    assert sparse.error.message
    assert MutationResult._from_json({"key": "d", "error": "nonsense"}).error is None
