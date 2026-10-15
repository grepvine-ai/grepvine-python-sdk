"""Planning of list-form writes into batches and single uploads.

Text documents travel in NDJSON batches of at most 2,048 records and 16 MiB of
content. Binary or larger documents travel one at a time as multipart uploads.
Batches are flushed in input order, and the service answers every document of
a batch in request order, so results line up with the input.
"""

from __future__ import annotations

import json
import os
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import IO, Any, Final, Required, TypeAlias, TypedDict

from grepvine._core.metadata import MetadataInput, document_metadata

MAX_BATCH_RECORDS: Final = 2048
MAX_BATCH_CONTENT_BYTES: Final = 16 * 1024 * 1024
MAX_LINE_BYTES: Final = 60 * 1024 * 1024

Content: TypeAlias = bytes | bytearray | memoryview | str | os.PathLike[str] | IO[bytes]
"""Document content: bytes, text, a filesystem path, or a readable binary file object."""


class DocumentInput(TypedDict, total=False):
    """One document of a list-form ``put``."""

    key: Required[str]
    content: Required[Content]
    metadata: MetadataInput
    if_match: str
    if_none_match: bool


class DeleteInput(TypedDict, total=False):
    """One document of a list-form ``delete``."""

    key: Required[str]
    if_match: str


_PUT_KEYS: Final = frozenset({"key", "content", "metadata", "if_match", "if_none_match"})
_DELETE_KEYS: Final = frozenset({"key", "if_match"})


@dataclass(frozen=True, slots=True)
class PutRecord:
    ordinal: int
    key: str
    content: Content
    metadata: MetadataInput | None
    if_match: str | None
    if_none_match: bool


def normalize_put_inputs(documents: Iterable[DocumentInput | Mapping[str, Any]]) -> list[PutRecord]:
    records: list[PutRecord] = []
    for ordinal, document in enumerate(documents):
        if not isinstance(document, Mapping):
            raise TypeError(
                f"documents[{ordinal}] must be a mapping with 'key' and 'content', "
                f"not {type(document).__name__}"
            )
        unknown = sorted(set(document) - _PUT_KEYS)
        if unknown:
            raise ValueError(f"documents[{ordinal}] has unknown field(s): {', '.join(unknown)}")
        key = document.get("key")
        if not isinstance(key, str) or not key:
            raise ValueError(f"documents[{ordinal}] needs a non-empty string 'key'")
        if "content" not in document:
            raise ValueError(f"documents[{ordinal}] ({key!r}) needs 'content'")
        if_match = document.get("if_match")
        if if_match is not None and not isinstance(if_match, str):
            raise ValueError(f"documents[{ordinal}] ({key!r}): if_match must be a string")
        if_none_match = bool(document.get("if_none_match", False))
        if if_match is not None and if_none_match:
            raise ValueError(
                f"documents[{ordinal}] ({key!r}): if_match and if_none_match cannot be combined"
            )
        records.append(
            PutRecord(
                ordinal=ordinal,
                key=key,
                content=document["content"],
                metadata=document.get("metadata"),
                if_match=if_match,
                if_none_match=if_none_match,
            )
        )
    return records


def normalize_delete_inputs(
    keys: Iterable[str | DeleteInput | Mapping[str, Any]],
) -> list[tuple[str, str | None]]:
    records: list[tuple[str, str | None]] = []
    for ordinal, entry in enumerate(keys):
        if isinstance(entry, str):
            if not entry:
                raise ValueError(f"keys[{ordinal}] must not be empty")
            records.append((entry, None))
            continue
        if not isinstance(entry, Mapping):
            raise TypeError(
                f"keys[{ordinal}] must be a key or a mapping with 'key', not {type(entry).__name__}"
            )
        unknown = sorted(set(entry) - _DELETE_KEYS)
        if unknown:
            raise ValueError(f"keys[{ordinal}] has unknown field(s): {', '.join(unknown)}")
        key = entry.get("key")
        if not isinstance(key, str) or not key:
            raise ValueError(f"keys[{ordinal}] needs a non-empty string 'key'")
        if_match = entry.get("if_match")
        if if_match is not None and not isinstance(if_match, str):
            raise ValueError(f"keys[{ordinal}] ({key!r}): if_match must be a string")
        records.append((key, if_match))
    return records


class FileWindow:
    """The tail of a seekable binary file, from a fixed start position, as its own file object.

    The HTTP library rewinds a file part to position zero before sending it,
    which would drop the caller's current position. This view maps position
    zero onto start so a file object is sent from where the caller left it.
    """

    def __init__(self, file: IO[bytes], start: int) -> None:
        self._file = file
        self._start = start

    def read(self, size: int = -1) -> bytes:
        return self._file.read(size)

    def seek(self, offset: int, whence: int = os.SEEK_SET) -> int:
        if whence == os.SEEK_SET:
            position = self._file.seek(self._start + offset)
        else:
            position = self._file.seek(offset, whence)
            if position < self._start:
                position = self._file.seek(self._start)
        return position - self._start

    def tell(self) -> int:
        return self._file.tell() - self._start

    def seekable(self) -> bool:
        return True


@dataclass(frozen=True, slots=True)
class LoadedContent:
    """Content ready for a multipart upload."""

    data: bytes | IO[bytes] | FileWindow
    size: int
    start: int
    mtime: datetime | None
    owned: IO[bytes] | None = None
    """A file the SDK opened itself and must close after the upload."""


def load_content(content: Content) -> LoadedContent:
    """Prepare content for a multipart upload without reading files into memory when avoidable.

    A path is opened for reading and the caller closes it (``close`` is True).
    A seekable file object is sent from its current position and rewound there
    before every attempt; a non-seekable one is read into memory.
    """
    if isinstance(content, str):
        data = content.encode("utf-8")
        return LoadedContent(data, len(data), 0, None)
    if isinstance(content, bytes | bytearray | memoryview):
        data = bytes(content)
        return LoadedContent(data, len(data), 0, None)
    if isinstance(content, os.PathLike):
        path = os.fspath(content)
        stat = os.stat(path)
        handle = open(path, "rb")  # noqa: SIM115 - closed by the operation after the upload
        return LoadedContent(
            handle,
            stat.st_size,
            0,
            datetime.fromtimestamp(stat.st_mtime, tz=UTC),
            owned=handle,
        )
    if hasattr(content, "read"):
        seekable = getattr(content, "seekable", None)
        if callable(seekable) and seekable():
            start = content.tell()
            end = content.seek(0, os.SEEK_END)
            content.seek(start)
            window = FileWindow(content, start) if start else content
            return LoadedContent(window, end - start, 0, None)
        data = content.read()
        if not isinstance(data, bytes):
            raise TypeError("file objects must be opened in binary mode")
        return LoadedContent(data, len(data), 0, None)
    raise TypeError(
        f"content must be bytes, str, a path, or a binary file object, not {type(content).__name__}"
    )


def as_text(content: Content) -> str | None:
    """The content as text when it is text, else None."""
    if isinstance(content, str):
        return content
    if isinstance(content, bytes | bytearray | memoryview):
        try:
            return bytes(content).decode("utf-8")
        except UnicodeDecodeError:
            return None
    return None


@dataclass(frozen=True, slots=True)
class BatchChunk:
    """One NDJSON batch."""

    records: tuple[PutRecord, ...]
    ndjson: bytes

    @property
    def keys(self) -> list[str]:
        return [record.key for record in self.records]


@dataclass(frozen=True, slots=True)
class SingleUpload:
    """One document that travels alone as a multipart upload."""

    record: PutRecord

    @property
    def keys(self) -> list[str]:
        return [self.record.key]


def ndjson_line(record: PutRecord, text: str) -> tuple[bytes, int]:
    """One batch record as an NDJSON line, with its UTF-8 content length."""
    content_bytes = len(text.encode("utf-8"))
    body: dict[str, Any] = {
        "key": record.key,
        "content": text,
        "metadata": document_metadata(record.key, content_bytes, record.metadata),
    }
    if record.if_match is not None:
        body["if_match"] = record.if_match
    if record.if_none_match:
        body["if_none_match"] = "*"
    return json.dumps(body, ensure_ascii=False).encode("utf-8") + b"\n", content_bytes


def plan_batches(records: Iterable[PutRecord]) -> list[BatchChunk | SingleUpload]:
    """Group records into bounded batches and single uploads, preserving input order."""
    plan: list[BatchChunk | SingleUpload] = []
    pending: list[PutRecord] = []
    pending_lines: list[bytes] = []
    pending_bytes = 0

    def flush() -> None:
        nonlocal pending, pending_lines, pending_bytes
        if pending:
            plan.append(BatchChunk(tuple(pending), b"".join(pending_lines)))
        pending, pending_lines, pending_bytes = [], [], 0

    for record in records:
        text = as_text(record.content)
        line: bytes | None = None
        content_bytes = 0
        if text is not None:
            line, content_bytes = ndjson_line(record, text)
            if content_bytes > MAX_BATCH_CONTENT_BYTES or len(line) > MAX_LINE_BYTES:
                line = None
        if line is None:
            flush()
            plan.append(SingleUpload(record))
            continue
        if (
            len(pending) >= MAX_BATCH_RECORDS
            or pending_bytes + content_bytes > MAX_BATCH_CONTENT_BYTES
        ):
            flush()
        pending.append(record)
        pending_lines.append(line)
        pending_bytes += content_bytes
    flush()
    return plan
