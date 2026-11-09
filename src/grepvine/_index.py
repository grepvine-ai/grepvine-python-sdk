"""`IndexClient`: one index, bound to its organization and name."""

from __future__ import annotations

import builtins
import io
import json
import mimetypes
import os
import uuid
from collections.abc import AsyncIterable, AsyncIterator, Iterable, Iterator, Mapping
from typing import IO, Any
from urllib.parse import quote

from grepvine import _helpers, _retry
from grepvine._generated.api.resources import _AsyncIndexClient, _IndexClient
from grepvine._generated.client import Client as _Connection
from grepvine._generated.models import DocumentSummary, Index, MutationResult
from grepvine._generated.types import File
from grepvine._helpers import DocumentInput, MetadataValue, Prefix

__all__ = ["AsyncContent", "AsyncIndexClient", "Content", "IndexClient"]

CHUNK_SIZE = 64 * 1024
Content = str | bytes | os.PathLike[str] | IO[bytes] | Iterable[bytes]
"""Content for ``put``: text, bytes, a path to a file, a binary file object, or byte chunks."""
AsyncContent = Content | AsyncIterable[bytes]
"""Content for ``AsyncIndexClient.put``: any `Content`, or an async iterable of byte chunks."""


def split(name: str) -> tuple[str, str]:
    """``"acme/support"`` as ``("acme", "support")``."""
    organization, _, index = name.partition("/")
    if not organization or not index or "/" in index:
        raise ValueError(f"name an index as 'organization/index', not {name!r}")
    return organization, index


def _tags(metadata: Mapping[str, MetadataValue] | None) -> dict[str, Any] | None:
    if metadata is None:
        return None
    return {name: _helpers._tag(value) for name, value in metadata.items()}


def _file_name(key: str) -> str:
    return os.path.basename(key) or key


def _put_arguments(
    key: str,
    payload: Any,
    metadata: Mapping[str, MetadataValue] | None,
    if_match: str | None,
    if_none_match: bool,
) -> dict[str, Any]:
    return {
        "key": key,
        "content": File(payload=payload, file_name=_file_name(key)),
        "metadata": _tags(metadata),
        "if_match": if_match,
        "if_none_match": "*" if if_none_match else None,
    }


def _in_memory(content: object) -> io.BytesIO | None:
    """Text or bytes as a file the SDK can send again on a retry."""
    if isinstance(content, str):
        return io.BytesIO(content.encode())
    if isinstance(content, bytes | bytearray | memoryview):
        return io.BytesIO(bytes(content))
    return None


def _seekable(content: object) -> bool:
    try:
        return hasattr(content, "read") and bool(content.seekable())  # type: ignore[attr-defined]
    except (AttributeError, ValueError):
        return False


def _chunks(content: object) -> Iterator[bytes]:
    """A one-way stream's bytes: a file object that cannot seek, or an iterable of chunks."""
    if hasattr(content, "read"):
        reader: Any = content
        yield from iter(lambda: reader.read(CHUNK_SIZE), b"")
        return
    if isinstance(content, Iterable):
        for chunk in content:
            yield _chunk(chunk)
        return
    raise TypeError(
        "content must be str, bytes, a path, a binary file, or an iterable of bytes, "
        f"not {type(content).__name__}"
    )


def _chunk(chunk: object) -> bytes:
    if isinstance(chunk, bytes | bytearray | memoryview):
        return bytes(chunk)
    raise TypeError(f"each chunk of content must be bytes, not {type(chunk).__name__}")


class _Counter:
    """Counts a stream's bytes and checks them against the size the caller gave."""

    def __init__(self, size: int | None) -> None:
        self.size = size
        self.sent = 0

    def add(self, chunk: bytes) -> bytes:
        self.sent += len(chunk)
        if self.size is not None and self.sent > self.size:
            raise ValueError(f"the content is longer than size={self.size}")
        return chunk

    def finish(self) -> None:
        if self.size is not None and self.sent != self.size:
            raise ValueError(f"the content has {self.sent} bytes, not size={self.size}")


def _form_value(value: str) -> str:
    """A quoted form parameter's value, escaped as HTML forms and httpx escape it."""
    escaped = value.replace("\\", "\\\\").replace('"', "%22")
    return "".join(f"%{ord(c):02X}" if ord(c) < 0x20 and c != "\x1b" else c for c in escaped)


class _Form:
    """The multipart form of ``put`` around content that is streamed, not held in memory."""

    def __init__(
        self,
        organization: str,
        index: str,
        key: str,
        metadata: Mapping[str, MetadataValue] | None,
        if_match: str | None,
        if_none_match: bool,
        size: int | None,
    ) -> None:
        boundary = uuid.uuid4().hex
        name = _form_value(_file_name(key))
        kind = mimetypes.guess_type(name)[0] or "application/octet-stream"
        parts = [
            f'--{boundary}\r\nContent-Disposition: form-data; name="key"\r\n'
            f"Content-Type: text/plain\r\n\r\n".encode()
            + key.encode()
            + b"\r\n"
        ]
        if (tags := _tags(metadata)) is not None:
            parts.append(
                f'--{boundary}\r\nContent-Disposition: form-data; name="metadata"\r\n'
                "Content-Type: application/json\r\n\r\n".encode()
                + json.dumps(tags).encode()
                + b"\r\n"
            )
        parts.append(
            f'--{boundary}\r\nContent-Disposition: form-data; name="content"; '
            f'filename="{name}"\r\nContent-Type: {kind}\r\n\r\n'.encode()
        )
        self.head = b"".join(parts)
        self.tail = f"\r\n--{boundary}--\r\n".encode()
        self.counter = _Counter(size)
        self.path = (
            f"/organizations/{quote(organization, safe='')}/indexes/{quote(index, safe='')}/objects"
        )
        self.headers = {"Content-Type": f"multipart/form-data; boundary={boundary}"}
        if size is not None:
            self.headers["Content-Length"] = str(len(self.head) + size + len(self.tail))
        if if_match is not None:
            self.headers["If-Match"] = if_match
        if if_none_match:
            self.headers["If-None-Match"] = "*"

    def body(self, chunks: Iterable[bytes]) -> Iterator[bytes]:
        yield self.head
        for chunk in chunks:
            yield self.counter.add(chunk)
        self.counter.finish()
        yield self.tail

    async def async_body(self, chunks: AsyncIterable[bytes]) -> AsyncIterator[bytes]:
        yield self.head
        async for chunk in chunks:
            yield self.counter.add(_chunk(chunk))
        self.counter.finish()
        yield self.tail


async def _async_chunks(chunks: Iterable[bytes]) -> AsyncIterator[bytes]:
    for chunk in chunks:
        yield chunk


_PUT_DOC = """Store one document of up to 1 GiB, text or binary.

        ``content`` is one of:

        - ``str`` or ``bytes``: the content itself;
        - a ``pathlib.Path`` (any ``os.PathLike``): the file at that path, streamed;
        - a binary file object, such as ``open(path, "rb")`` or ``io.BytesIO``: streamed
          from where it is;
        - an iterable of ``bytes`` chunks, such as a generator: streamed as it is produced.

        A plain ``str`` is always content, never a path. Text, bytes, paths and files that
        can seek are sent again when an attempt fails and is retried. Content read from a
        stream (chunks, or a file that cannot seek, such as a pipe) is sent once: a failed
        attempt raises its error, and ``put`` must be called again with the content.

        ``size`` is the length in bytes of streamed content, when known. Pass it for large or
        slow uploads: without it, the upload must finish within 35 seconds; with it, the
        service allows longer in proportion to the size. Content of another length raises
        ``ValueError``.

        Metadata values are ``str``, ``bool``, ``int``, ``float`` or ``datetime``.
        ``if_match`` stores the document only over that revision; ``if_none_match`` only when
        the key is new.
        """


class IndexClient(_IndexClient):
    """One index: its documents, search and settings.

    ``client.index("acme/support")`` makes one without sending a request.
    """

    def __init__(self, connection: _Connection, name: str, documents: _helpers.Documents) -> None:
        super().__init__(connection, *split(name))
        self._documents = documents

    @property
    def name(self) -> str:
        """The index as ``organization/index``."""
        return f"{self._organization}/{self._index}"

    def __repr__(self) -> str:
        return f"IndexClient({self.name!r})"

    def put(
        self,
        key: str,
        content: Content,
        *,
        size: int | None = None,
        metadata: Mapping[str, MetadataValue] | None = None,
        if_match: str | None = None,
        if_none_match: bool = False,
    ) -> MutationResult:
        if isinstance(content, AsyncIterable):
            raise TypeError("content that is an async iterable needs an AsyncClient")
        if isinstance(content, os.PathLike):
            with open(content, "rb") as file:
                return self._put(**_put_arguments(key, file, metadata, if_match, if_none_match))
        payload = _in_memory(content) or (content if _seekable(content) else None)
        if payload is not None:
            return self._put(**_put_arguments(key, payload, metadata, if_match, if_none_match))
        form = _Form(self._organization, self._index, key, metadata, if_match, if_none_match, size)
        with _retry.one_way():
            response = self._client.get_httpx_client().put(
                form.path, content=form.body(_chunks(content)), headers=form.headers
            )
        return MutationResult.from_dict(response.json())

    put.__doc__ = _PUT_DOC

    def put_many(
        self, documents: Iterable[DocumentInput], *, idempotency_key: str | None = None
    ) -> builtins.list[MutationResult]:
        """Store text documents in as few requests as possible; see ``Documents.put_many``."""
        return self._documents.put_many(
            self._organization, self._index, documents, idempotency_key=idempotency_key
        )

    def list(
        self,
        *,
        prefix: str | None = None,
        delimiter: str | None = None,
        amount: int | None = None,
    ) -> Iterator[DocumentSummary | Prefix]:
        """List documents in key order, page after page; see ``Documents.list``."""
        return self._documents.list(
            self._organization, self._index, prefix=prefix, delimiter=delimiter, amount=amount
        )

    def wait_until_ready(self, *, timeout: float | None = 300.0, interval: float = 1.0) -> Index:
        """Wait until an index created elsewhere is ready, and return it.

        After ``create``, call ``wait()`` on the `IndexCreation` it returns instead. Raises the
        same errors; see ``Indexes.wait_until_ready``.
        """
        started = _retry.monotonic()
        while not _helpers._check_state(
            found := self.info(), _retry.monotonic() - started, timeout
        ):
            _retry.sleep(interval)
        return found


class AsyncIndexClient(_AsyncIndexClient):
    """One index, for an `AsyncClient`; see `IndexClient`."""

    def __init__(
        self, connection: _Connection, name: str, documents: _helpers.AsyncDocuments
    ) -> None:
        super().__init__(connection, *split(name))
        self._documents = documents

    @property
    def name(self) -> str:
        """The index as ``organization/index``."""
        return f"{self._organization}/{self._index}"

    def __repr__(self) -> str:
        return f"AsyncIndexClient({self.name!r})"

    async def put(
        self,
        key: str,
        content: AsyncContent,
        *,
        size: int | None = None,
        metadata: Mapping[str, MetadataValue] | None = None,
        if_match: str | None = None,
        if_none_match: bool = False,
    ) -> MutationResult:
        if isinstance(content, os.PathLike):
            with open(content, "rb") as file:
                return await self._put(
                    **_put_arguments(key, file, metadata, if_match, if_none_match)
                )
        payload = _in_memory(content) or (content if _seekable(content) else None)
        if payload is not None:
            return await self._put(
                **_put_arguments(key, payload, metadata, if_match, if_none_match)
            )
        form = _Form(self._organization, self._index, key, metadata, if_match, if_none_match, size)
        chunks = content if isinstance(content, AsyncIterable) else _async_chunks(_chunks(content))
        with _retry.one_way():
            response = await self._client.get_async_httpx_client().put(
                form.path, content=form.async_body(chunks), headers=form.headers
            )
        return MutationResult.from_dict(response.json())

    put.__doc__ = _PUT_DOC.replace("Store one document", "Store one document, awaited,").replace(
        "- an iterable of ``bytes`` chunks, such as a generator: streamed as it is produced.",
        "- an iterable or async iterable of ``bytes`` chunks, such as a generator: streamed\n"
        "          as it is produced.",
    )

    async def put_many(
        self, documents: Iterable[DocumentInput], *, idempotency_key: str | None = None
    ) -> builtins.list[MutationResult]:
        """Store text documents in batches; see ``Documents.put_many``."""
        return await self._documents.put_many(
            self._organization, self._index, documents, idempotency_key=idempotency_key
        )

    def list(
        self,
        *,
        prefix: str | None = None,
        delimiter: str | None = None,
        amount: int | None = None,
    ) -> AsyncIterator[DocumentSummary | Prefix]:
        """List documents in key order, page after page; see ``Documents.list``."""
        return self._documents.list(
            self._organization, self._index, prefix=prefix, delimiter=delimiter, amount=amount
        )

    async def wait_until_ready(
        self, *, timeout: float | None = 300.0, interval: float = 1.0
    ) -> Index:
        """Wait until an index created elsewhere is ready; see ``IndexClient.wait_until_ready``."""
        started = _retry.monotonic()
        while not _helpers._check_state(
            found := await self.info(), _retry.monotonic() - started, timeout
        ):
            await _retry.async_sleep(interval)
        return found
