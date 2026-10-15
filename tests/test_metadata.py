from __future__ import annotations

from datetime import UTC, date, datetime, timedelta, timezone

import pytest

from grepvine._core.metadata import (
    MAX_FIELDS,
    default_metadata,
    document_metadata,
    format_timestamp,
    tag,
    tag_value,
    untag,
)


def test_tag_infers_types() -> None:
    when = datetime(2026, 9, 6, 12, 30, tzinfo=timezone(timedelta(hours=2)))
    assert tag({"s": "x", "i": 3, "f": 1.5, "b": False, "t": when}) == {
        "s": {"type": "string", "value": "x"},
        "i": {"type": "integer", "value": 3},
        "f": {"type": "number", "value": 1.5},
        "b": {"type": "boolean", "value": False},
        "t": {"type": "timestamp", "value": "2026-09-06T10:30:00Z"},
    }


def test_format_timestamp() -> None:
    assert format_timestamp(datetime(2026, 1, 1, 0, 0, 0)) == "2026-01-01T00:00:00Z"
    assert (
        format_timestamp(datetime(2026, 1, 1, 0, 0, 0, 500000, tzinfo=UTC))
        == "2026-01-01T00:00:00.500000Z"
    )


def test_tag_passes_tagged_values_through() -> None:
    assert tag_value({"type": "timestamp", "value": "2026-01-01T00:00:00Z"}) == {
        "type": "timestamp",
        "value": "2026-01-01T00:00:00Z",
    }
    with pytest.raises(ValueError, match="tagged metadata value"):
        tag_value({"type": "date", "value": "x"})
    with pytest.raises(ValueError, match="tagged metadata value"):
        tag_value({"type": "string"})


def test_tag_rejects_unsupported_values() -> None:
    with pytest.raises(ValueError, match="64-bit"):
        tag_value(2**63)
    with pytest.raises(ValueError, match="must be str, int, float, bool or datetime"):
        tag_value(None)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="must be str, int, float, bool or datetime"):
        tag_value(date(2026, 1, 1))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="field names"):
        tag({"": 1})


def test_untag() -> None:
    plain = untag(
        {
            "s": {"type": "string", "value": "x"},
            "t": {"type": "timestamp", "value": "2026-01-01T00:00:00Z"},
            "bad": {"type": "timestamp", "value": "not a date"},
            "odd": {"type": "mystery", "value": 7},
            "raw": 5,
        }
    )
    assert plain["s"] == "x"
    assert plain["t"] == datetime(2026, 1, 1, tzinfo=UTC)
    assert plain["bad"] == "not a date"
    assert plain["odd"] == 7
    assert plain["raw"] == 5
    assert untag(None) == {}
    assert untag({}) == {}


def test_document_metadata_merges_defaults() -> None:
    assert default_metadata("k", 3) == {
        "path": {"type": "string", "value": "k"},
        "size": {"type": "integer", "value": 3},
    }
    merged = document_metadata("k", 3, {"size": 99, "lang": "en"}, datetime(2026, 1, 1, tzinfo=UTC))
    assert merged["size"] == {"type": "integer", "value": 99}
    assert merged["lang"] == {"type": "string", "value": "en"}
    assert merged["mtime"] == {"type": "timestamp", "value": "2026-01-01T00:00:00Z"}
    with pytest.raises(ValueError, match=f"at most {MAX_FIELDS}"):
        document_metadata("k", 1, {f"f{n}": n for n in range(MAX_FIELDS)})
