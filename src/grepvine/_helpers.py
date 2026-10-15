"""Pagination, waiting and batch uploads, added to the API's resources."""

from __future__ import annotations

import inspect
import io
import json
from collections.abc import AsyncIterator, Awaitable, Callable, Iterable, Iterator, Mapping
from datetime import UTC, datetime
from typing import Any, Final, Protocol, Required, TypeAlias, TypedDict, TypeVar, overload

from grepvine import _retry
from grepvine._generated.api import resources
from grepvine._generated.models import (
    APIKeyCreated,
    DeviceAuthorization,
    DeviceAuthorizationRequest,
    DeviceTokenRequest,
    Index,
    IndexState,
    MutationResult,
    Pagination,
)
from grepvine._generated.types import UNSET, File
from grepvine.errors import GrepvineError, InvalidRequestError, PartialBatchError

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


class _Page(Protocol[T]):
    results: list[T]
    pagination: Pagination


@overload
def paginate(method: Callable[..., Awaitable[_Page[T]]], /, **params: Any) -> AsyncIterator[T]: ...
@overload
def paginate(method: Callable[..., _Page[T]], /, **params: Any) -> Iterator[T]: ...
def paginate(method: Callable[..., Any], /, **params: Any) -> Any:
    """Iterate over every result of a list or search method, page after page.

    Pass the method and its arguments by name, for example
    ``paginate(client.indexes.list, organization="acme")``. Iteration follows
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


def _tag(value: MetadataValue) -> dict[str, Any]:
    """The API's tagged form of a metadata value; ``bool`` is tested before ``int``."""
    if isinstance(value, datetime):
        stamp = (value if value.tzinfo else value.replace(tzinfo=UTC)).astimezone(UTC)
        return {"type": "timestamp", "value": stamp.isoformat().replace("+00:00", "Z")}
    for kind, tag in ((bool, "boolean"), (int, "integer"), (float, "number"), (str, "string")):
        if isinstance(value, kind):
            return {"type": tag, "value": value}
    raise TypeError(f"metadata values must be str, int, float, bool or datetime, not {value!r}")


def _batches(documents: Iterable[DocumentInput]) -> list[tuple[list[str], bytes]]:
    """Group documents into NDJSON bodies of at most 2,048 documents and 16 MiB of content."""
    batches: list[tuple[list[str], bytes]] = []
    keys: list[str] = []
    lines: list[bytes] = []
    size = 0
    for document in documents:
        key, content = document["key"], document["content"]
        text = content.decode("utf-8") if isinstance(content, bytes) else content
        length = len(text.encode("utf-8"))
        if length > MAX_BATCH_BYTES:
            raise ValueError(f"{key!r} is larger than 16 MiB; store it with documents.put")
        if keys and (len(keys) == MAX_BATCH_DOCUMENTS or size + length > MAX_BATCH_BYTES):
            batches.append((keys, b"".join(lines)))
            keys, lines, size = [], [], 0
        metadata = {"path": _tag(key), "size": _tag(length)}
        metadata.update((name, _tag(value)) for name, value in document.get("metadata", {}).items())
        record: dict[str, Any] = {"key": key, "content": text, "metadata": metadata}
        if "if_match" in document:
            record["if_match"] = document["if_match"]
        if document.get("if_none_match"):
            record["if_none_match"] = "*"
        keys.append(key)
        lines.append(json.dumps(record, ensure_ascii=False).encode("utf-8") + b"\n")
        size += length
    if keys:
        batches.append((keys, b"".join(lines)))
    return batches


def _batch_arguments(body: bytes, idempotency_key: str | None, position: int) -> dict[str, Any]:
    return {
        "body": File(payload=io.BytesIO(body), mime_type="application/x-ndjson"),
        "idempotency_key": f"{idempotency_key}-{position}" if idempotency_key else UNSET,
    }


def _partial(
    results: list[MutationResult],
    batches: list[tuple[list[str], bytes]],
    position: int,
    cause: GrepvineError,
) -> GrepvineError:
    if not results:
        return cause
    pending = [key for keys, _ in batches[position + 1 :] for key in keys]
    return PartialBatchError(
        committed=results, failed_keys=batches[position][0], pending_keys=pending, cause=cause
    )


def _check_state(index: Index, waited: float, timeout: float) -> bool:
    if index.state == IndexState.READY:
        return True
    if index.state != IndexState.CREATING:
        raise GrepvineError(f"index {index.organization}/{index.name} is {index.state}")
    if waited >= timeout:
        raise TimeoutError(f"index {index.organization}/{index.name} was not ready in {timeout:g}s")
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
        self, organization: str, index: str, *, timeout: float = 300.0, interval: float = 1.0
    ) -> Index:
        """Read the index until it is ready, and return it.

        Raises:
            TimeoutError: The index was not ready within ``timeout`` seconds.
            grepvine.GrepvineError: The index is being deleted and will never be ready.
        """
        started = _retry.monotonic()
        while not _check_state(
            found := self.get(organization, index), _retry.monotonic() - started, timeout
        ):
            _retry.sleep(interval)
        return found


class AsyncIndexes(resources.AsyncIndexes):
    async def wait_until_ready(
        self, organization: str, index: str, *, timeout: float = 300.0, interval: float = 1.0
    ) -> Index:
        """Read the index until it is ready, and return it; see ``Indexes.wait_until_ready``."""
        started = _retry.monotonic()
        while not _check_state(
            found := await self.get(organization, index), _retry.monotonic() - started, timeout
        ):
            await _retry.async_sleep(interval)
        return found


class Documents(resources.Documents):
    def put_many(
        self,
        organization: str,
        index: str,
        documents: Iterable[DocumentInput],
        *,
        idempotency_key: str | None = None,
    ) -> list[MutationResult]:
        """Store text documents in as few requests as the batch limits allow.

        Each document gets ``path`` (its key) and ``size`` metadata, overlaid
        with its own ``metadata``. Returns one result per document, in input
        order; a document the service left unchanged has an ``error`` there.
        With ``idempotency_key`` (16 characters or more), repeating a failed
        call with the same documents applies none of them twice.

        Raises:
            grepvine.PartialBatchError: A request failed after earlier ones succeeded.
        """
        batches = _batches(documents)
        results: list[MutationResult] = []
        for position, (_, body) in enumerate(batches):
            try:
                answer = self.put_batch(
                    organization, index, **_batch_arguments(body, idempotency_key, position)
                )
            except GrepvineError as exc:
                raise _partial(results, batches, position, exc) from exc
            results.extend(answer.results)
        return results


class AsyncDocuments(resources.AsyncDocuments):
    async def put_many(
        self,
        organization: str,
        index: str,
        documents: Iterable[DocumentInput],
        *,
        idempotency_key: str | None = None,
    ) -> list[MutationResult]:
        """Store text documents in batches; see ``Documents.put_many``."""
        batches = _batches(documents)
        results: list[MutationResult] = []
        for position, (_, body) in enumerate(batches):
            try:
                answer = await self.put_batch(
                    organization, index, **_batch_arguments(body, idempotency_key, position)
                )
            except GrepvineError as exc:
                raise _partial(results, batches, position, exc) from exc
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
            TimeoutError: The login was not approved within ``timeout`` seconds.
        """
        authorization = self.start(body=DeviceAuthorizationRequest(api_key_name=api_key_name))
        on_code(authorization)
        interval, deadline = _poll_interval(authorization, timeout)
        while _retry.monotonic() + interval <= deadline:
            _retry.sleep(interval)
            try:
                return self.poll(body=DeviceTokenRequest(device_code=authorization.device_code))
            except InvalidRequestError as exc:
                interval = _next_poll(exc, interval)
        raise TimeoutError("the device login was not approved in time")


class AsyncDeviceLogin(resources.AsyncDeviceLogin):
    async def authorize(
        self,
        api_key_name: str,
        *,
        on_code: Callable[[DeviceAuthorization], object],
        timeout: float | None = None,
    ) -> APIKeyCreated:
        """Start a device login and poll until the key is issued; see ``DeviceLogin.authorize``."""
        authorization = await self.start(body=DeviceAuthorizationRequest(api_key_name=api_key_name))
        on_code(authorization)
        interval, deadline = _poll_interval(authorization, timeout)
        while _retry.monotonic() + interval <= deadline:
            await _retry.async_sleep(interval)
            try:
                return await self.poll(
                    body=DeviceTokenRequest(device_code=authorization.device_code)
                )
            except InvalidRequestError as exc:
                interval = _next_poll(exc, interval)
        raise TimeoutError("the device login was not approved in time")
