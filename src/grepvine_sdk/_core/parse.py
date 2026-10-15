"""Reading a document from the headers and body of a read."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from typing import Any, Protocol

from grepvine_sdk._core.metadata import untag
from grepvine_sdk.models import ContentRange, Document

_CONTENT_RANGE = re.compile(r"^bytes\s+(\d+)-(\d+)/(\d+|\*)$")


class DocumentResponse(Protocol):
    @property
    def status_code(self) -> int: ...

    @property
    def headers(self) -> Mapping[str, str]: ...

    @property
    def content(self) -> bytes: ...


def revision_from_etag(value: str | None) -> str:
    """The revision carried by an ``ETag`` header, with any weak marker and quotes removed."""
    if not value:
        return ""
    revision = value.strip()
    if revision.startswith("W/"):
        revision = revision[2:]
    if len(revision) >= 2 and revision[0] == revision[-1] == '"':
        revision = revision[1:-1]
    return revision


def content_range(value: str | None) -> ContentRange | None:
    if not value:
        return None
    match = _CONTENT_RANGE.match(value.strip())
    if match is None:
        return None
    start, end, total = match.groups()
    return ContentRange(int(start), int(end), int(total) if total != "*" else int(end) + 1)


def metadata_header(raw: str | None) -> dict[str, Any]:
    """The plain metadata of the ``X-Grepvine-Metadata`` header; empty when absent or unreadable."""
    if not raw:
        return {}
    try:
        decoded = json.loads(raw)
    except ValueError:
        return {}
    return untag(decoded) if isinstance(decoded, Mapping) else {}


def document(response: DocumentResponse, key: str) -> Document:
    headers = response.headers
    return Document(
        key=key,
        revision=revision_from_etag(headers.get("etag")),
        content=response.content,
        metadata=metadata_header(headers.get("x-grepvine-metadata")),
        content_range=content_range(headers.get("content-range"))
        if response.status_code == 206
        else None,
    )
