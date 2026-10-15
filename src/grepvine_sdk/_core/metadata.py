"""Conversion between plain Python metadata and the API's tagged values.

The API stores every metadata field as ``{"type": ..., "value": ...}``. The
SDK accepts plain values and infers the tag: ``str`` is a string, ``bool`` a
boolean, ``int`` an integer, ``float`` a number, and ``datetime`` a timestamp.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any, Final, TypeAlias

MetadataValue: TypeAlias = str | int | float | bool | datetime
"""A plain metadata value the SDK can tag."""

MetadataInput: TypeAlias = Mapping[str, "MetadataValue | Mapping[str, Any]"]
"""Metadata as given to the SDK: plain values, or already tagged ``{"type", "value"}`` objects."""

TYPE_TAGS: Final = frozenset({"string", "integer", "number", "boolean", "timestamp"})
MAX_FIELDS: Final = 64
_INT64_MIN: Final = -(2**63)
_INT64_MAX: Final = 2**63 - 1


def format_timestamp(value: datetime) -> str:
    """Render a datetime as RFC 3339 in UTC; a naive datetime is taken as UTC."""
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    value = value.astimezone(UTC)
    text = value.isoformat()
    return text[: -len("+00:00")] + "Z" if text.endswith("+00:00") else text


def tag_value(value: MetadataValue | Mapping[str, Any]) -> dict[str, Any]:
    """Tag one plain value; an already tagged object passes through after a check."""
    if isinstance(value, Mapping):
        tag = value.get("type")
        if tag not in TYPE_TAGS or "value" not in value:
            raise ValueError(
                "a tagged metadata value needs a 'type' of string, integer, number, "
                "boolean or timestamp and a 'value'"
            )
        return {"type": tag, "value": value["value"]}
    if isinstance(value, bool):
        return {"type": "boolean", "value": value}
    if isinstance(value, int):
        if not _INT64_MIN <= value <= _INT64_MAX:
            raise ValueError("integer metadata must fit in a signed 64-bit integer")
        return {"type": "integer", "value": value}
    if isinstance(value, float):
        return {"type": "number", "value": value}
    if isinstance(value, datetime):
        return {"type": "timestamp", "value": format_timestamp(value)}
    if isinstance(value, str):
        return {"type": "string", "value": value}
    raise ValueError(
        f"metadata values must be str, int, float, bool or datetime, not {type(value).__name__}"
    )


def tag(metadata: MetadataInput) -> dict[str, dict[str, Any]]:
    """Tag every value of a metadata mapping."""
    tagged: dict[str, dict[str, Any]] = {}
    for name, value in metadata.items():
        if not name:
            raise ValueError("metadata field names must be non-empty strings")
        tagged[name] = tag_value(value)
    return tagged


def untag_value(wire: Any) -> Any:
    """Turn one tagged value back into a plain value; unknown shapes are returned as they are."""
    if not isinstance(wire, Mapping) or "value" not in wire:
        return wire
    value = wire["value"]
    if wire.get("type") == "timestamp" and isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return value
    return value


def untag(wire: Mapping[str, Any] | None) -> dict[str, Any]:
    """Turn a tagged metadata object into a plain dict."""
    if not wire:
        return {}
    return {name: untag_value(value) for name, value in wire.items()}


def default_metadata(
    key: str, size: int, mtime: datetime | None = None
) -> dict[str, dict[str, Any]]:
    """The metadata the SDK attaches to every stored document.

    ``path`` and ``size`` match what ``gv upload`` records, so filters such as
    ``path STARTSWITH 'src/'`` work on documents stored from Python too.
    """
    metadata: dict[str, dict[str, Any]] = {
        "path": {"type": "string", "value": key},
        "size": {"type": "integer", "value": size},
    }
    if mtime is not None:
        metadata["mtime"] = {"type": "timestamp", "value": format_timestamp(mtime)}
    return metadata


def document_metadata(
    key: str, size: int, user_metadata: MetadataInput | None, mtime: datetime | None = None
) -> dict[str, dict[str, Any]]:
    """Default metadata overlaid with the caller's, whose fields win."""
    merged = default_metadata(key, size, mtime)
    if user_metadata:
        merged.update(tag(user_metadata))
    if len(merged) > MAX_FIELDS:
        raise ValueError(f"a document may carry at most {MAX_FIELDS} metadata fields")
    return merged
