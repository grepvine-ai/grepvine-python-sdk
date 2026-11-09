"""Pagination, waiting and batch uploads, added to the API's resources."""

from __future__ import annotations

import builtins
import inspect
import io
import json
import math
from collections.abc import (
    AsyncIterator,
    Awaitable,
    Callable,
    Iterable,
    Iterator,
    Mapping,
    Sequence,
)
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Final, Protocol, Required, TypeAlias, TypedDict, TypeVar, overload

from grepvine import _retry
from grepvine._generated.api import resources
from grepvine._generated.models import (
    APIKeyCreated,
    DeviceAuthorization,
    DocumentPage,
    DocumentSummary,
    Index,
    IndexState,
    MutationResult,
    Pagination,
)
from grepvine._generated.types import File
from grepvine.errors import (
    GrepvineError,
    InvalidRequestError,
    OperationFailedError,
    PartialBatchError,
    WaitTimeoutError,
)

T = TypeVar("T")
MAX_BATCH_DOCUMENTS: Final = 2048
MAX_BATCH_BYTES: Final = 16 * 1024 * 1024
SLOW_DOWN_STEP: Final = 5.0
__all__ = [
    "AsyncDeviceLogin",
    "AsyncDocuments",
    "AsyncIndexes",
    "DeviceLogin",
    "DocumentInput",
    "Documents",
    "Indexes",
    "MetadataValue",
    "Prefix",
    "paginate",
]

MetadataValue: TypeAlias = str | int | float | bool | datetime
"""A metadata value: ``str``, ``bool``, ``int``, ``float``, or ``datetime`` for a timestamp."""


class DocumentInput(TypedDict, total=False):
    """One document for ``documents.put_many``.

    ``content`` is text, or UTF-8 encoded bytes. ``if_match`` stores the
    document only over that revision; ``if_none_match`` only when the key is
    new.
    """

    key: Required[str]
    content: Required[str | bytes]
    metadata: Mapping[str, MetadataValue]
    if_match: str
    if_none_match: bool


@dataclass(frozen=True)
class Prefix:
    """A common prefix of a listing with a ``delimiter``: its keys, folded like a folder."""

    prefix: str


def _entries(page: DocumentPage) -> Iterator[DocumentSummary | Prefix]:
    """A page's common prefixes, then its documents, as ``gv list`` prints them."""
    for prefix in page.common_prefixes:
        yield Prefix(prefix)
    yield from page.results


class _Page(Protocol[T]):
    results: list[T]
    pagination: Pagination


@overload
def paginate(method: Callable[..., Awaitable[_Page[T]]], /, **params: Any) -> AsyncIterator[T]: ...
@overload
def paginate(method: Callable[..., _Page[T]], /, **params: Any) -> Iterator[T]: ...
def paginate(method: Callable[..., Any], /, **params: Any) -> Any:
    """Iterate over every result of a list or search method, page after page.

    Pass a ``_page`` method and its arguments by name, for example
    ``paginate(client.indexes.list_page, organization="acme")``. Iteration follows
    each page's ``pagination.next_page_id`` while ``has_next`` is true, also
    across pages that hold no results. With an ``AsyncClient`` method, iterate
    with ``async for``.
    """
    if inspect.iscoroutinefunction(method):
        return _async_pages(method, params)
    return _pages(method, params)


def _pages(method: Callable[..., Any], params: dict[str, Any]) -> Iterator[Any]:
    while True:
        page = method(**params)
        yield from page.results
        if not page.pagination.has_next:
            return
        params = {**params, "page": page.pagination.next_page_id}


async def _async_pages(method: Callable[..., Any], params: dict[str, Any]) -> AsyncIterator[Any]:
    while True:
        page = await method(**params)
        for item in page.results:
            yield item
        if not page.pagination.has_next:
            return
        params = {**params, "page": page.pagination.next_page_id}


def _page_sequence(
    method: Callable[..., Any], args: tuple[Any, ...], options: dict[str, Any]
) -> Iterator[Any]:
    """Every page of a ``_page`` method, following ``next_page_id`` while ``has_next``."""
    while True:
        page = method(*args, **options)
        yield page
        if not page.pagination.has_next:
            return
        options = {**options, "page": page.pagination.next_page_id}


async def _async_page_sequence(
    method: Callable[..., Any], args: tuple[Any, ...], options: dict[str, Any]
) -> AsyncIterator[Any]:
    while True:
        page = await method(*args, **options)
        yield page
        if not page.pagination.has_next:
            return
        options = {**options, "page": page.pagination.next_page_id}


def _tag(value: MetadataValue) -> dict[str, Any]:
    """The API's tagged form of a metadata value; ``bool`` is tested before ``int``."""
    if isinstance(value, datetime):
        stamp = (value if value.tzinfo else value.replace(tzinfo=UTC)).astimezone(UTC)
        return {"type": "timestamp", "value": stamp.isoformat().replace("+00:00", "Z")}
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError(f"metadata numbers must be finite, not {value!r}")
    for kind, tag in ((bool, "boolean"), (int, "integer"), (float, "number"), (str, "string")):
        if isinstance(value, kind):
            return {"type": tag, "value": value}
    raise TypeError(f"metadata values must be str, int, float, bool or datetime, not {value!r}")


def _encode(document: DocumentInput) -> tuple[str, bytes, int]:
    """One document as an NDJSON line, with its key and its content's length in bytes."""
    key, content = document["key"], document["content"]
    if isinstance(content, bytes):
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            raise ValueError(f"{key!r} is not UTF-8 text; store binary content with put") from None
    elif isinstance(content, str):
        text = content
    else:
        raise TypeError(f"{key!r}: content must be str or bytes, not {type(content).__name__}")
    length = len(text.encode("utf-8"))
    if length > MAX_BATCH_BYTES:
        raise ValueError(f"{key!r} is larger than 16 MiB; store it with put")
    metadata = {"path": _tag(key), "size": _tag(length)}
    metadata.update((name, _tag(value)) for name, value in document.get("metadata", {}).items())
    record: dict[str, Any] = {"key": key, "content": text, "metadata": metadata}
    if "if_match" in document:
        record["if_match"] = document["if_match"]
    if document.get("if_none_match"):
        record["if_none_match"] = "*"
    return key, json.dumps(record, ensure_ascii=False).encode("utf-8") + b"\n", length


class _Batches:
    """Reads documents into NDJSON bodies of at most 2,048 documents and 16 MiB of content.

    Documents are read one batch at a time, so a generator is never held in memory whole.
    """

    def __init__(self, documents: Iterable[DocumentInput]) -> None:
        self._sequence = documents if isinstance(documents, Sequence) else None
        self._documents = iter(documents)
        self._read = 0
        self._ahead: tuple[str, bytes, int] | None = None

    def __iter__(self) -> Iterator[tuple[list[str], bytes]]:
        keys: list[str] = []
        lines: list[bytes] = []
        size = 0
        while True:
            if self._ahead is None:
                document = next(self._documents, None)
                if document is None:
                    break
                self._read += 1
                self._ahead = _encode(document)
            key, line, length = self._ahead
            if keys and (len(keys) == MAX_BATCH_DOCUMENTS or size + length > MAX_BATCH_BYTES):
                yield keys, b"".join(lines)
                keys, lines, size = [], [], 0
            self._ahead = None
            keys.append(key)
            lines.append(line)
            size += length
        if keys:
            yield keys, b"".join(lines)

    def pending(self) -> list[str]:
        """Keys not sent: the document read ahead, and the rest of a list or tuple."""
        keys = [self._ahead[0]] if self._ahead else []
        if self._sequence is not None:
            keys.extend(document["key"] for document in self._sequence[self._read :])
        return keys


def _batch_arguments(body: bytes, idempotency_key: str | None, position: int) -> dict[str, Any]:
    return {
        "body": File(payload=io.BytesIO(body), mime_type="application/x-ndjson"),
        "idempotency_key": f"{idempotency_key}-{position}" if idempotency_key else None,
    }


def _partial(
    results: list[MutationResult], keys: list[str], batches: _Batches, cause: GrepvineError
) -> GrepvineError:
    if not results:
        return cause
    return PartialBatchError(
        committed=results, failed_keys=keys, pending_keys=batches.pending(), cause=cause
    )


def _check_state(index: Index, waited: float, timeout: float | None) -> bool:
    target = f"index {index.organization}/{index.name}"
    if index.state == IndexState.READY:
        return True
    if index.state != IndexState.CREATING:
        raise OperationFailedError(target=target, state=str(index.state))
    if timeout is not None and waited >= timeout:
        raise WaitTimeoutError(target=target, state=str(index.state), timeout=timeout)
    return False


def _next_poll(error: InvalidRequestError, interval: float) -> float:
    if error.code == "slow_down":
        return interval + SLOW_DOWN_STEP
    if error.code == "authorization_pending":
        return interval
    raise error


def _poll_interval(
    authorization: DeviceAuthorization, timeout: float | None
) -> tuple[float, float]:
    limit = authorization.expires_in if timeout is None else min(timeout, authorization.expires_in)
    return max(float(authorization.interval), 1.0), _retry.monotonic() + limit


class Indexes(resources.Indexes):
    def wait_until_ready(
        self, organization: str, index: str, *, timeout: float | None = 300.0, interval: float = 1.0
    ) -> Index:
        """Read the index until it is ready, and return it.

        ``timeout`` is in seconds; ``None`` waits without a limit.

        Raises:
            grepvine.WaitTimeoutError: The index was not ready within ``timeout`` seconds.
            grepvine.OperationFailedError: The index is being deleted and will never be ready.
        """
        started = _retry.monotonic()
        while not _check_state(
            found := self.get(organization, index), _retry.monotonic() - started, timeout
        ):
            _retry.sleep(interval)
        return found


class AsyncIndexes(resources.AsyncIndexes):
    async def wait_until_ready(
        self, organization: str, index: str, *, timeout: float | None = 300.0, interval: float = 1.0
    ) -> Index:
        """Read the index until it is ready, and return it; see ``Indexes.wait_until_ready``."""
        started = _retry.monotonic()
        while not _check_state(
            found := await self.get(organization, index), _retry.monotonic() - started, timeout
        ):
            await _retry.async_sleep(interval)
        return found


class Documents(resources.Documents):
    def list(
        self,
        organization: str,
        index: str,
        *,
        prefix: str | None = None,
        delimiter: str | None = None,
        amount: int | None = None,
    ) -> Iterator[DocumentSummary | Prefix]:
        """List documents, page after page, in key order.

        With a ``delimiter``, keys that share the text up to the next delimiter after ``prefix``
        are folded into one `Prefix`, yielded before the documents of the same page.
        """
        options = {"prefix": prefix, "delimiter": delimiter, "amount": amount}
        for page in _page_sequence(self.list_page, (organization, index), options):
            yield from _entries(page)

    def put_many(
        self,
        organization: str,
        index: str,
        documents: Iterable[DocumentInput],
        *,
        idempotency_key: str | None = None,
    ) -> builtins.list[MutationResult]:
        """Store text documents in as few requests as the batch limits allow.

        ``documents`` may be a list or any iterable, such as a generator: it is
        read one batch at a time, so at most about 16 MiB of content is held in
        memory. Each document gets ``path`` (its key) and ``size`` metadata,
        overlaid with its own ``metadata``. Returns one result per document, in
        input order; a document the service left unchanged has an ``error``
        there. With ``idempotency_key`` (16 characters or more), repeating a
        failed call with the same documents applies none of them twice.

        Raises:
            grepvine.PartialBatchError: A request failed after earlier ones succeeded.
            ValueError: A document is not UTF-8 text or is over 16 MiB; store it with
                ``put``. Documents are checked as they are read, so earlier batches may
                already be stored.
        """
        batches = _Batches(documents)
        results: builtins.list[MutationResult] = []
        for position, (keys, body) in enumerate(batches):
            try:
                answer = self.put_batch(
                    organization, index, **_batch_arguments(body, idempotency_key, position)
                )
            except GrepvineError as exc:
                raise _partial(results, keys, batches, exc) from exc
            results.extend(answer.results)
        return results


class AsyncDocuments(resources.AsyncDocuments):
    async def list(
        self,
        organization: str,
        index: str,
        *,
        prefix: str | None = None,
        delimiter: str | None = None,
        amount: int | None = None,
    ) -> AsyncIterator[DocumentSummary | Prefix]:
        """List documents, page after page; see ``Documents.list``."""
        options = {"prefix": prefix, "delimiter": delimiter, "amount": amount}
        async for page in _async_page_sequence(self.list_page, (organization, index), options):
            for entry in _entries(page):
                yield entry

    async def put_many(
        self,
        organization: str,
        index: str,
        documents: Iterable[DocumentInput],
        *,
        idempotency_key: str | None = None,
    ) -> builtins.list[MutationResult]:
        """Store text documents in batches; see ``Documents.put_many``."""
        batches = _Batches(documents)
        results: builtins.list[MutationResult] = []
        for position, (keys, body) in enumerate(batches):
            try:
                answer = await self.put_batch(
                    organization, index, **_batch_arguments(body, idempotency_key, position)
                )
            except GrepvineError as exc:
                raise _partial(results, keys, batches, exc) from exc
            results.extend(answer.results)
        return results


class DeviceLogin(resources.DeviceLogin):
    def authorize(
        self,
        api_key_name: str,
        *,
        on_code: Callable[[DeviceAuthorization], object],
        timeout: float | None = None,
    ) -> APIKeyCreated:
        """Start a device login, report its code, and poll until the API key is issued.

        ``on_code`` receives the authorization to show the user: its
        ``verification_uri_complete`` and ``user_code``. Polling follows the
        service's interval and slows down when asked to.

        Raises:
            grepvine.InvalidRequestError: The login was denied (code ``"access_denied"``)
                or expired (``"expired_token"``).
            grepvine.WaitTimeoutError: The login was not approved within ``timeout`` seconds,
                or before it expired.
        """
        authorization = self.start(api_key_name=api_key_name)
        on_code(authorization)
        interval, deadline = _poll_interval(authorization, timeout)
        while _retry.monotonic() + interval <= deadline:
            _retry.sleep(interval)
            try:
                return self.poll(device_code=authorization.device_code)
            except InvalidRequestError as exc:
                interval = _next_poll(exc, interval)
        raise WaitTimeoutError(
            target="device login",
            state="authorization_pending",
            timeout=authorization.expires_in if timeout is None else timeout,
        )


class AsyncDeviceLogin(resources.AsyncDeviceLogin):
    async def authorize(
        self,
        api_key_name: str,
        *,
        on_code: Callable[[DeviceAuthorization], object],
        timeout: float | None = None,
    ) -> APIKeyCreated:
        """Start a device login and poll until the key is issued; see ``DeviceLogin.authorize``."""
        authorization = await self.start(api_key_name=api_key_name)
        on_code(authorization)
        interval, deadline = _poll_interval(authorization, timeout)
        while _retry.monotonic() + interval <= deadline:
            await _retry.async_sleep(interval)
            try:
                return await self.poll(device_code=authorization.device_code)
            except InvalidRequestError as exc:
                interval = _next_poll(exc, interval)
        raise WaitTimeoutError(
            target="device login",
            state="authorization_pending",
            timeout=authorization.expires_in if timeout is None else timeout,
        )
