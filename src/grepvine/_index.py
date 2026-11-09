"""`IndexClient`: one index, bound to its organization and name."""

from __future__ import annotations

import builtins
import io
import os
from collections.abc import AsyncIterator, Iterable, Iterator, Mapping
from typing import IO, Any

from grepvine import _helpers, _retry
from grepvine._generated.api.resources import _AsyncIndexClient, _IndexClient
from grepvine._generated.client import Client as _Connection
from grepvine._generated.models import DocumentSummary, Index, MutationResult
from grepvine._generated.types import File
from grepvine._helpers import DocumentInput, MetadataValue, Prefix

__all__ = ["AsyncIndexClient", "IndexClient"]

Content = str | bytes | IO[bytes]


def split(name: str) -> tuple[str, str]:
    """``"acme/support"`` as ``("acme", "support")``."""
    organization, _, index = name.partition("/")
    if not organization or not index or "/" in index:
        raise ValueError(f"name an index as 'organization/index', not {name!r}")
    return organization, index


def _put_arguments(
    key: str,
    content: Content,
    metadata: Mapping[str, MetadataValue] | None,
    if_match: str | None,
    if_none_match: bool,
) -> dict[str, Any]:
    if isinstance(content, str):
        content = content.encode()
    payload: Any = io.BytesIO(content) if isinstance(content, bytes) else content
    return {
        "key": key,
        "content": File(payload=payload, file_name=os.path.basename(key) or key),
        "metadata": None
        if metadata is None
        else {name: _helpers._tag(value) for name, value in metadata.items()},
        "if_match": if_match,
        "if_none_match": "*" if if_none_match else None,
    }


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
        metadata: Mapping[str, MetadataValue] | None = None,
        if_match: str | None = None,
        if_none_match: bool = False,
    ) -> MutationResult:
        """Store one document of up to 1 GiB, text or binary.

        ``content`` is text, bytes, or a binary file object. Metadata values are ``str``,
        ``bool``, ``int``, ``float`` or ``datetime``. ``if_match`` stores the document only over
        that revision; ``if_none_match`` only when the key is new.
        """
        return self._put(**_put_arguments(key, content, metadata, if_match, if_none_match))

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

    def wait_until_ready(self, *, timeout: float = 300.0, interval: float = 1.0) -> Index:
        """Read the index until it is ready, and return it; see ``Indexes.wait_until_ready``."""
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
        content: Content,
        *,
        metadata: Mapping[str, MetadataValue] | None = None,
        if_match: str | None = None,
        if_none_match: bool = False,
    ) -> MutationResult:
        """Store one document of up to 1 GiB; see ``IndexClient.put``."""
        return await self._put(**_put_arguments(key, content, metadata, if_match, if_none_match))

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

    async def wait_until_ready(self, *, timeout: float = 300.0, interval: float = 1.0) -> Index:
        """Read the index until it is ready, and return it; see ``Indexes.wait_until_ready``."""
        started = _retry.monotonic()
        while not _helpers._check_state(
            found := await self.info(), _retry.monotonic() - started, timeout
        ):
            await _retry.async_sleep(interval)
        return found
