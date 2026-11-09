"""Fields the service leaves out read as None, or [] for a list; None is left out of requests."""

from __future__ import annotations

import grepvine
from grepvine.models import APIKey, DeleteObjectRecord, MutationResult, QueryResult

HIT = {
    "key": "a.txt",
    "revision": "r1",
    "line_number": 1,
    "last_line_number": 1,
    "line_start_offset": 0,
    "line_end_offset": 5,
    "text_start_offset": 0,
    "text_line_number": 1,
    "text": "hello",
    "matches": [],
    "text_truncated": False,
    "matches_truncated": False,
}


def test_absent_fields_are_none() -> None:
    key = APIKey.from_dict(
        {
            "id": "00000000-0000-0000-0000-000000000001",
            "name": "ci",
            "prefix": "gvk_1234",
            "created_at": "2026-01-01T00:00:00Z",
        }
    )
    assert key.revoked_at is None and key.last_used_at is None
    assert "Unset" not in repr(key)
    assert MutationResult.from_dict({"key": "a"}).error is None


def test_absent_lists_are_empty() -> None:
    hit = QueryResult.from_dict(HIT)
    assert hit.lines_before == [] and hit.lines_after == []
    assert [line.text for line in hit.lines_before] == []


def test_present_fields_are_kept() -> None:
    hit = QueryResult.from_dict(
        HIT | {"lines_before": [{"line_number": 0, "text": "x", "text_truncated": False}]}
    )
    assert [line.text for line in hit.lines_before] == ["x"]
    assert MutationResult.from_dict({"key": "a", "revision": "r2"}).revision == "r2"


def test_none_is_left_out_of_a_request() -> None:
    assert DeleteObjectRecord(key="a").to_dict() == {"key": "a"}
    assert DeleteObjectRecord.from_dict({"key": "a"}).to_dict() == {"key": "a"}
    assert DeleteObjectRecord(key="a", if_match="r1").to_dict() == {"key": "a", "if_match": "r1"}


def test_round_trip_keeps_what_was_sent() -> None:
    hit = QueryResult.from_dict(HIT)
    assert QueryResult.from_dict(hit.to_dict()) == hit


def test_settings_show_the_api_key_only_in_part() -> None:
    settings = grepvine.Client(api_key="gvk_0123456789abcdef", trust_env=False).settings
    assert "gvk_0123456789abcdef" not in repr(settings)
    assert "gvk_0123****" in repr(settings) and "gvk_0123****" in str(settings)
    short = grepvine.Client(api_key="gvk_short", trust_env=False).settings
    assert "gvk_short" not in repr(short) and "'****'" in repr(short)
    assert settings.api_key == "gvk_0123456789abcdef"
