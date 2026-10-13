import asyncio
import json
import time
from datetime import UTC, datetime
from typing import Any

import httpx
import pytest

from grepvine_sdk import ApiError, AsyncGrepvineClient, BatchError, GrepvineClient, MetadataInput

ERROR = {"code": "busy", "reason": "capacity", "error": "Slow down and retry."}
INDEX = {
    "id": "00000000-0000-4000-8000-000000000001",
    "organization": "acme",
    "name": "docs",
    "canonical_id": "acme/docs",
    "description": "",
    "tags": {},
    "state": "creating",
    "document_count": 0,
    "content_bytes": 0,
    "created_at": "2026-10-13T12:00:00Z",
    "last_updated_at": "2026-10-13T12:00:00Z",
}


@pytest.mark.parametrize("asynchronous", [False, True])
def test_upload_helpers_and_partial_failures(asynchronous: bool) -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.method == "PUT":
            return httpx.Response(200, json={"key": "a.bin", "revision": "r1"})
        return httpx.Response(
            200,
            headers={"X-Request-ID": "req-batch"},
            json={
                "results": [
                    {"key": "a", "revision": "r1"},
                    {
                        "key": "b",
                        "error": {
                            "code": "precondition_failed",
                            "reason": "revision",
                            "error": "Check revision",
                        },
                    },
                ]
            },
        )

    documents: Any = [
        {"key": "a", "content": "hello\nworld", "metadata": {"kind": "guide", "flag": True}},
        {"key": "b", "content": "bye", "if_match": "old"},
    ]
    metadata: MetadataInput = {
        "kind": "guide",
        "flag": True,
        "count": 3,
        "score": 1.5,
        "created": datetime(2026, 10, 13, tzinfo=UTC),
    }

    def assertions() -> None:
        assert requests[0].headers["Authorization"] == "Bearer gvk_test"
        assert requests[0].headers["Idempotency-Key"]  # automatically generated
        assert requests[0].headers["If-None-Match"] == "*"
        assert b'"type": "boolean"' in requests[0].content
        assert b'"type": "timestamp"' in requests[0].content
        body = requests[1].content.decode()
        assert len(body.splitlines()) == 2
        records = [json.loads(line) for line in body.splitlines()]
        assert records[0]["content"] == "hello\nworld"
        assert records[0]["metadata"]["flag"] == {"type": "boolean", "value": True}
        assert records[1]["if_match"] == "old"
        assert requests[1].headers["Idempotency-Key"] == "stable-operation-123"
        assert requests[1].content == requests[2].content  # caller can replay the exact batch
        assert requests[2].headers["Idempotency-Key"] == "stable-operation-123"

    def check_batch(error: BatchError) -> None:
        assert len(error.results) == 2 and error.results[0].revision == "r1"
        assert [failure.key for failure in error.failures] == ["b"]
        assert error.request_id == "req-batch"

    if asynchronous:

        async def run() -> None:
            async with AsyncGrepvineClient(
                api_key="gvk_test",
                endpoint="https://example.test",
                httpx_args={"transport": httpx.MockTransport(handler)},
            ) as client:
                index = client.indexes.get("acme/docs")
                await index.documents.put(
                    "a.bin", b"\x00\xff", metadata=metadata, if_none_match=True
                )
                with pytest.raises(BatchError) as caught:
                    await index.documents.put_many(
                        documents, idempotency_key="stable-operation-123"
                    )
                check_batch(caught.value)
                results = await index.documents.put_many(
                    documents, idempotency_key="stable-operation-123", raise_on_error=False
                )
                assert len(results) == 2
                connection = client.raw.get_async_httpx_client()
            assert connection.is_closed

        asyncio.run(run())
    else:
        with GrepvineClient(
            api_key="gvk_test",
            endpoint="https://example.test",
            httpx_args={"transport": httpx.MockTransport(handler)},
        ) as client:
            index = client.indexes.get("acme/docs")
            index.documents.put("a.bin", b"\x00\xff", metadata=metadata, if_none_match=True)
            with pytest.raises(BatchError) as caught:
                index.documents.put_many(documents, idempotency_key="stable-operation-123")
            check_batch(caught.value)
            assert (
                len(
                    index.documents.put_many(
                        documents, idempotency_key="stable-operation-123", raise_on_error=False
                    )
                )
                == 2
            )
            connection = client.raw.get_httpx_client()
        assert connection.is_closed
    assertions()


@pytest.mark.parametrize("asynchronous", [False, True])
def test_api_errors_are_actionable_and_not_retried(asynchronous: bool) -> None:
    requests = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(
            429, json=ERROR, headers={"X-Request-ID": "req-123", "Retry-After": "2"}
        )

    if asynchronous:

        async def run() -> None:
            async with AsyncGrepvineClient(
                api_key="gvk", httpx_args={"transport": httpx.MockTransport(handler)}
            ) as client:
                with pytest.raises(ApiError) as caught:
                    await client.indexes.get("acme/docs").documents.put("a", "hello")
                assert caught.value.status == 429 and caught.value.code == "busy"
                assert caught.value.request_id == "req-123" and caught.value.retry_after == 2

        asyncio.run(run())
    else:
        with GrepvineClient(
            api_key="gvk", httpx_args={"transport": httpx.MockTransport(handler)}
        ) as client:
            with pytest.raises(ApiError) as caught:
                client.indexes.get("acme/docs").documents.put("a", "hello")
            assert caught.value.status == 429 and caught.value.code == "busy"
            assert caught.value.request_id == "req-123" and caught.value.retry_after == 2
    assert len(requests) == 1


@pytest.mark.parametrize("asynchronous", [False, True])
def test_search_follows_empty_continuations_with_unchanged_options(asynchronous: bool) -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        last = len(requests) == 3
        return httpx.Response(
            200,
            json={
                "results": [],
                "pagination": {
                    "has_next": not last,
                    "next_page_id": "" if last else f"token-{len(requests)}",
                },
            },
        )

    if asynchronous:

        async def run() -> None:
            async with AsyncGrepvineClient(
                api_key="gvk", httpx_args={"transport": httpx.MockTransport(handler)}
            ) as client:
                assert [
                    hit
                    async for hit in client.indexes.get("acme/docs").search(
                        "hello",
                        literal=True,
                        filter="kind = 'guide'",
                        amount=1,
                        lines_before=2,
                    )
                ] == []

        asyncio.run(run())
    else:
        with GrepvineClient(
            api_key="gvk", httpx_args={"transport": httpx.MockTransport(handler)}
        ) as client:
            assert (
                list(
                    client.indexes.get("acme/docs").search(
                        "hello",
                        literal=True,
                        filter="kind = 'guide'",
                        amount=1,
                        lines_before=2,
                    )
                )
                == []
            )
    assert [request.url.params.get("page") for request in requests] == [None, "token-1", "token-2"]
    assert all(request.content == requests[0].content for request in requests)
    assert json.loads(requests[0].content)["filter"] == "kind = 'guide'"
    assert json.loads(requests[0].content)["lines_before"] == 2


@pytest.mark.parametrize("asynchronous", [False, True])
def test_invalid_batch_is_rejected_before_any_write(asynchronous: bool) -> None:
    requests = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        raise AssertionError("No request should be sent")

    if asynchronous:

        async def run() -> None:
            async with AsyncGrepvineClient(
                api_key="gvk", httpx_args={"transport": httpx.MockTransport(handler)}
            ) as client:
                documents = client.indexes.get("acme/docs").documents
                with pytest.raises(ValueError, match="2048"):
                    await documents.put_many({"key": str(n), "content": "a"} for n in range(2049))
                with pytest.raises(ValueError, match="16 MiB"):
                    await documents.put_many([{"key": "a", "content": "é" * (8 * 1024 * 1024 + 1)}])

        asyncio.run(run())
    else:
        with GrepvineClient(
            api_key="gvk", httpx_args={"transport": httpx.MockTransport(handler)}
        ) as client:
            documents = client.indexes.get("acme/docs").documents
            with pytest.raises(ValueError, match="2048"):
                documents.put_many({"key": str(n), "content": "a"} for n in range(2049))
            with pytest.raises(ValueError, match="16 MiB"):
                documents.put_many([{"key": "a", "content": "é" * (8 * 1024 * 1024 + 1)}])
    assert not requests


def test_sync_readiness_limits_io_and_restores_the_normal_timeout() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json=INDEX)

    with GrepvineClient(
        api_key="gvk", timeout=10, httpx_args={"transport": httpx.MockTransport(handler)}
    ) as client:
        index = client.indexes.get("acme/docs")
        with pytest.raises(TimeoutError):
            index.wait_ready(timeout=0.01, interval=0.001)
        assert all(request.extensions["timeout"]["read"] <= 0.01 for request in requests)
        index.info()
        assert requests[-1].extensions["timeout"]["read"] == 10


def test_async_readiness_and_cancellation_do_not_block_the_event_loop() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        await asyncio.sleep(1)
        return httpx.Response(200, json=INDEX)

    async def run() -> None:
        async with AsyncGrepvineClient(
            api_key="gvk", httpx_args={"transport": httpx.MockTransport(handler)}
        ) as client:
            started = time.monotonic()
            with pytest.raises(TimeoutError):
                await client.indexes.get("acme/docs").wait_ready(timeout=0.01)
            assert time.monotonic() - started < 0.5
            task = asyncio.create_task(client.indexes.get("acme/docs").documents.put("a", "hello"))
            await asyncio.sleep(0)
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task

    asyncio.run(run())
