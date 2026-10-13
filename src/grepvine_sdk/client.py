"""Resource handles over the generated sync and async operations."""

import asyncio
import math
import time
from collections.abc import AsyncIterator, Iterable, Iterator, Mapping
from contextvars import ContextVar
from typing import Any, BinaryIO, Self

import httpx

from ._common import (
    Document,
    MetadataInput,
    batch_body,
    checked,
    endpoint_url,
    form,
    make_idempotency_key,
    mutation,
    mutations,
    poll_options,
    query,
    reference,
    unwrap,
    write_options,
)
from .generated.api.indexes import create_index, delete_index, get_index
from .generated.api.objects import put_document, put_objects
from .generated.api.search import query_index
from .generated.client import AuthenticatedClient
from .generated.models import (
    CreateIndexRequest,
    Index,
    IndexState,
    IndexTags,
    MutationBatchResult,
    MutationResult,
    QueryPage,
    QueryResult,
)
from .generated.types import UNSET, Unset


class GrepvineClient:
    """Synchronous convenience client. raw exposes the generated client."""

    def __init__(
        self,
        *,
        api_key: str,
        endpoint: str = "https://api.grepvine.ai",
        timeout: float = 30,
        httpx_args: dict[str, Any] | None = None,
    ) -> None:
        if not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("Request timeout must be positive and finite")
        self._deadline: ContextVar[float | None] = ContextVar(
            "grepvine_request_deadline", default=None
        )
        arguments = dict(httpx_args or {})
        hooks = {name: list(values) for name, values in arguments.get("event_hooks", {}).items()}
        hooks.setdefault("request", []).append(self._limit_request)
        arguments["event_hooks"] = hooks
        self.raw = AuthenticatedClient(
            base_url=endpoint_url(endpoint),
            token=api_key,
            timeout=httpx.Timeout(timeout),
            httpx_args=arguments,
        )
        self.indexes = Indexes(self)

    def _limit_request(self, request: httpx.Request) -> None:
        deadline = self._deadline.get()
        if deadline is not None:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("The readiness timeout expired")
            # Bound in-flight I/O without changing a shared client's timeout.
            current = request.extensions.get("timeout", {})
            request.extensions["timeout"] = {
                name: min(value, remaining) if value is not None else remaining
                for name, value in current.items()
            }

    def __enter__(self) -> Self:
        self.raw.__enter__()
        return self

    def close(self) -> None:
        self.raw.get_httpx_client().close()

    def __exit__(self, *args: Any) -> None:
        self.close()


class AsyncGrepvineClient:
    """Asynchronous convenience client. Use async with and async for."""

    def __init__(
        self,
        *,
        api_key: str,
        endpoint: str = "https://api.grepvine.ai",
        timeout: float = 30,
        httpx_args: dict[str, Any] | None = None,
    ) -> None:
        if not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("Request timeout must be positive and finite")
        self.raw = AuthenticatedClient(
            base_url=endpoint_url(endpoint),
            token=api_key,
            timeout=httpx.Timeout(timeout),
            httpx_args=httpx_args or {},
        )
        self.indexes = AsyncIndexes(self)

    async def __aenter__(self) -> Self:
        await self.raw.__aenter__()
        return self

    async def aclose(self) -> None:
        await self.raw.get_async_httpx_client().aclose()

    async def __aexit__(self, *args: Any) -> None:
        await self.aclose()


class Indexes:
    def __init__(self, client: GrepvineClient) -> None:
        self.client = client

    def get(self, ref: str) -> "IndexHandle":
        """Build a handle without an HTTP request; info fetches its current state."""
        return IndexHandle(self.client, ref)

    def create(
        self, ref: str, *, description: str | None = None, tags: Mapping[str, str] | None = None
    ) -> "IndexHandle":
        organization, name = reference(ref)
        unwrap(
            create_index.sync_detailed(
                organization,
                client=self.client.raw,
                body=CreateIndexRequest(
                    name=name,
                    description=description if description is not None else UNSET,
                    tags=IndexTags.from_dict(tags) if tags is not None else UNSET,
                ),
            ),
            Index,
        )
        return self.get(ref)


class AsyncIndexes:
    def __init__(self, client: AsyncGrepvineClient) -> None:
        self.client = client

    def get(self, ref: str) -> "AsyncIndexHandle":
        """Build a handle without an HTTP request; await info to fetch its state."""
        return AsyncIndexHandle(self.client, ref)

    async def create(
        self, ref: str, *, description: str | None = None, tags: Mapping[str, str] | None = None
    ) -> "AsyncIndexHandle":
        organization, name = reference(ref)
        unwrap(
            await create_index.asyncio_detailed(
                organization,
                client=self.client.raw,
                body=CreateIndexRequest(
                    name=name,
                    description=description if description is not None else UNSET,
                    tags=IndexTags.from_dict(tags) if tags is not None else UNSET,
                ),
            ),
            Index,
        )
        return self.get(ref)


class IndexHandle:
    def __init__(self, client: GrepvineClient, ref: str) -> None:
        self.client = client
        self.ref = ref
        self.organization, self.name = reference(ref)
        self.documents = Documents(self)

    def info(self) -> Index:
        return unwrap(
            get_index.sync_detailed(self.organization, self.name, client=self.client.raw), Index
        )

    def delete(self) -> None:
        checked(delete_index.sync_detailed(self.organization, self.name, client=self.client.raw))

    def wait_ready(self, *, timeout: float = 30, interval: float = 0.1) -> "IndexHandle":
        """Poll for readiness; HTTP requests also honor the client's request timeout."""
        poll_options(timeout, interval)
        deadline = time.monotonic() + timeout
        token = self.client._deadline.set(deadline)
        try:
            while time.monotonic() < deadline:
                info = self.info()
                if time.monotonic() >= deadline:
                    break
                if info.state == IndexState.READY:
                    return self
                if info.state != IndexState.CREATING:
                    raise RuntimeError(f"Index cannot become ready in state {info.state}")
                remaining = deadline - time.monotonic()
                if remaining > 0:
                    time.sleep(min(interval, remaining))
        except httpx.TimeoutException:
            if time.monotonic() < deadline:
                raise
        finally:
            self.client._deadline.reset(token)
        raise TimeoutError(f"Index {self.ref} did not become ready within {timeout} seconds")

    def search(
        self,
        pattern: str,
        *,
        filter: str | None = None,
        literal: bool = False,
        case_sensitive: bool = True,
        whole_word: bool = False,
        multiline: bool = False,
        lines_before: int = 0,
        lines_after: int = 0,
        amount: int = 200,
    ) -> Iterator[QueryResult]:
        body = query(
            pattern,
            filter=filter,
            literal=literal,
            case_sensitive=case_sensitive,
            whole_word=whole_word,
            multiline=multiline,
            lines_before=lines_before,
            lines_after=lines_after,
        )
        token: str | Unset = UNSET
        while True:
            response = unwrap(
                query_index.sync_detailed(
                    self.organization,
                    self.name,
                    client=self.client.raw,
                    body=body,
                    amount=amount,
                    page=token,
                ),
                QueryPage,
            )
            yield from response.results
            if not response.pagination.has_next:
                return
            token = response.pagination.next_page_id


class AsyncIndexHandle:
    def __init__(self, client: AsyncGrepvineClient, ref: str) -> None:
        self.client = client
        self.ref = ref
        self.organization, self.name = reference(ref)
        self.documents = AsyncDocuments(self)

    async def info(self) -> Index:
        return unwrap(
            await get_index.asyncio_detailed(self.organization, self.name, client=self.client.raw),
            Index,
        )

    async def delete(self) -> None:
        checked(
            await delete_index.asyncio_detailed(
                self.organization, self.name, client=self.client.raw
            )
        )

    async def wait_ready(self, *, timeout: float = 30, interval: float = 0.1) -> "AsyncIndexHandle":
        poll_options(timeout, interval)
        async with asyncio.timeout(timeout):
            while True:
                info = await self.info()
                if info.state == IndexState.READY:
                    return self
                if info.state != IndexState.CREATING:
                    raise RuntimeError(f"Index cannot become ready in state {info.state}")
                await asyncio.sleep(interval)

    async def search(
        self,
        pattern: str,
        *,
        filter: str | None = None,
        literal: bool = False,
        case_sensitive: bool = True,
        whole_word: bool = False,
        multiline: bool = False,
        lines_before: int = 0,
        lines_after: int = 0,
        amount: int = 200,
    ) -> AsyncIterator[QueryResult]:
        body = query(
            pattern,
            filter=filter,
            literal=literal,
            case_sensitive=case_sensitive,
            whole_word=whole_word,
            multiline=multiline,
            lines_before=lines_before,
            lines_after=lines_after,
        )
        token: str | Unset = UNSET
        while True:
            response = unwrap(
                await query_index.asyncio_detailed(
                    self.organization,
                    self.name,
                    client=self.client.raw,
                    body=body,
                    amount=amount,
                    page=token,
                ),
                QueryPage,
            )
            for hit in response.results:
                yield hit
            if not response.pagination.has_next:
                return
            token = response.pagination.next_page_id


class Documents:
    def __init__(self, index: IndexHandle) -> None:
        self.index = index

    def put(
        self,
        key: str,
        content: str | bytes | BinaryIO,
        *,
        metadata: MetadataInput | None = None,
        idempotency_key: str | None = None,
        if_match: str | None = None,
        if_none_match: bool = False,
    ) -> MutationResult:
        return mutation(
            put_document.sync_detailed(
                self.index.organization,
                self.index.name,
                client=self.index.client.raw,
                body=form(key, content, metadata),
                **write_options(idempotency_key, if_match, if_none_match),
            )
        )

    def put_many(
        self,
        documents: Iterable[Document],
        *,
        idempotency_key: str | None = None,
        raise_on_error: bool = True,
    ) -> list[MutationResult]:
        # One call is one batch. Encode it completely before sending anything.
        body = batch_body(documents)
        response = put_objects.sync_detailed(
            self.index.organization,
            self.index.name,
            client=self.index.client.raw,
            body=body,
            idempotency_key=make_idempotency_key(idempotency_key),
        )
        results = unwrap(response, MutationBatchResult).results
        return mutations(results, response.headers.get("X-Request-ID"), raise_on_error)


class AsyncDocuments:
    def __init__(self, index: AsyncIndexHandle) -> None:
        self.index = index

    async def put(
        self,
        key: str,
        content: str | bytes | BinaryIO,
        *,
        metadata: MetadataInput | None = None,
        idempotency_key: str | None = None,
        if_match: str | None = None,
        if_none_match: bool = False,
    ) -> MutationResult:
        return mutation(
            await put_document.asyncio_detailed(
                self.index.organization,
                self.index.name,
                client=self.index.client.raw,
                body=form(key, content, metadata),
                **write_options(idempotency_key, if_match, if_none_match),
            )
        )

    async def put_many(
        self,
        documents: Iterable[Document],
        *,
        idempotency_key: str | None = None,
        raise_on_error: bool = True,
    ) -> list[MutationResult]:
        body = batch_body(documents)
        response = await put_objects.asyncio_detailed(
            self.index.organization,
            self.index.name,
            client=self.index.client.raw,
            body=body,
            idempotency_key=make_idempotency_key(idempotency_key),
        )
        results = unwrap(response, MutationBatchResult).results
        return mutations(results, response.headers.get("X-Request-ID"), raise_on_error)
