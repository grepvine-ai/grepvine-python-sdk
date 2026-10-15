"""documents.put_many batches NDJSON, tags metadata and returns per-document results."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
import pytest

import grepvine
from grepvine.models import MutationResult
from tests.conftest import Flavor, Service, error

pytestmark = pytest.mark.anyio


def records(request: httpx.Request) -> list[dict[str, Any]]:
    return [json.loads(line) for line in request.content.decode().splitlines()]


def accept(request: httpx.Request) -> httpx.Response:
    """Store every record of a batch, answering in request order."""
    results = [
        {"key": record["key"], "revision": f"r-{record['key']}"} for record in records(request)
    ]
    return httpx.Response(200, json={"results": results})


async def test_one_batch_with_tagged_metadata(fx: Flavor, service: Service) -> None:
    service.route = accept
    stamp = datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone(timedelta(hours=2)))
    documents: list[grepvine.DocumentInput] = [
        {
            "key": "a.txt",
            "content": "héllo\n",
            "metadata": {"kind": "guide", "n": 3, "score": 0.5, "draft": True, "at": stamp},
        },
        {"key": "b.txt", "content": b"bytes\n", "if_match": "r0"},
        {"key": "c.txt", "content": "new\n", "if_none_match": True, "metadata": {"path": "x"}},
    ]
    results = await fx.run(fx.client.documents.put_many("acme", "docs", documents))
    assert [type(result) for result in results] == [MutationResult] * 3
    assert [(result.key, result.revision) for result in results] == [
        ("a.txt", "r-a.txt"),
        ("b.txt", "r-b.txt"),
        ("c.txt", "r-c.txt"),
    ]
    [request] = service.requests
    assert request.url.path == "/v1/organizations/acme/indexes/docs/objects:batch"
    assert request.headers["Content-Type"] == "application/x-ndjson"
    first, second, third = records(request)
    assert first == {
        "key": "a.txt",
        "content": "héllo\n",
        "metadata": {
            "path": {"type": "string", "value": "a.txt"},
            "size": {"type": "integer", "value": 7},
            "kind": {"type": "string", "value": "guide"},
            "n": {"type": "integer", "value": 3},
            "score": {"type": "number", "value": 0.5},
            "draft": {"type": "boolean", "value": True},
            "at": {"type": "timestamp", "value": "2026-01-02T01:04:05Z"},
        },
    }
    assert second["content"] == "bytes\n" and second["if_match"] == "r0"
    assert third["if_none_match"] == "*"
    assert third["metadata"]["path"] == {"type": "string", "value": "x"}


async def test_splits_at_2048_documents(fx: Flavor, service: Service) -> None:
    service.route = accept
    documents: list[grepvine.DocumentInput] = [{"key": f"{n}", "content": "x"} for n in range(4097)]
    results = await fx.run(fx.client.documents.put_many("acme", "docs", documents))
    assert [result.key for result in results] == [f"{n}" for n in range(4097)]
    assert [len(records(request)) for request in service.requests] == [2048, 2048, 1]
    keys = {request.headers["Idempotency-Key"] for request in service.requests}
    assert len(keys) == 3


async def test_splits_at_16_mib(fx: Flavor, service: Service) -> None:
    service.route = accept
    big = "x" * (6 * 1024 * 1024)
    documents: list[grepvine.DocumentInput] = [{"key": f"{n}", "content": big} for n in range(5)]
    await fx.run(fx.client.documents.put_many("acme", "docs", documents))
    assert [len(records(request)) for request in service.requests] == [2, 2, 1]


async def test_rejects_a_document_over_16_mib(fx: Flavor) -> None:
    documents: list[grepvine.DocumentInput] = [
        {"key": "big", "content": "x" * (16 * 1024 * 1024 + 1)}
    ]
    with pytest.raises(ValueError, match="documents.put"):
        await fx.run(fx.client.documents.put_many("acme", "docs", documents))


async def test_unchanged_documents_carry_an_error(fx: Flavor, service: Service) -> None:
    rejected = {"key": "a", "error": {"code": "precondition_failed", "reason": "r", "error": "no"}}
    service.reply(httpx.Response(200, json={"results": [rejected]}))
    [result] = await fx.run(
        fx.client.documents.put_many("acme", "docs", [{"key": "a", "content": "x"}])
    )
    assert result.error.code == "precondition_failed"


async def test_given_idempotency_key_is_numbered_per_batch(fx: Flavor, service: Service) -> None:
    service.route = accept
    documents: list[grepvine.DocumentInput] = [{"key": f"{n}", "content": "x"} for n in range(2049)]
    await fx.run(
        fx.client.documents.put_many("acme", "docs", documents, idempotency_key="job-0001-abcdef")
    )
    assert [request.headers["Idempotency-Key"] for request in service.requests] == [
        "job-0001-abcdef-0",
        "job-0001-abcdef-1",
    ]


async def test_failure_after_a_batch_reports_progress(fx: Flavor, service: Service) -> None:
    service.reply(accept, error(413, "too_large"))
    documents: list[grepvine.DocumentInput] = [{"key": f"{n}", "content": "x"} for n in range(4097)]
    with pytest.raises(grepvine.PartialBatchError) as raised:
        await fx.run(fx.client.documents.put_many("acme", "docs", documents))
    exc = raised.value
    assert len(exc.committed) == 2048
    assert exc.failed_keys == tuple(f"{n}" for n in range(2048, 4096))
    assert exc.pending_keys == ("4096",)
    assert isinstance(exc.__cause__, grepvine.PayloadTooLargeError)


async def test_failure_of_the_first_batch_raises_its_error(fx: Flavor, service: Service) -> None:
    service.reply(error(403, "permission_denied"))
    with pytest.raises(grepvine.PermissionDeniedError):
        await fx.run(fx.client.documents.put_many("acme", "docs", [{"key": "a", "content": "x"}]))


async def test_nothing_to_store(fx: Flavor, service: Service) -> None:
    assert await fx.run(fx.client.documents.put_many("acme", "docs", [])) == []
    assert service.requests == []


def test_rejects_unknown_metadata_types(service: Service) -> None:
    document: Any = {"key": "a", "content": "x", "metadata": {"x": [1]}}
    with grepvine.Client(transport=httpx.MockTransport(service.handle)) as client:
        with pytest.raises(TypeError):
            client.documents.put_many("acme", "docs", [document])
    assert service.requests == []
