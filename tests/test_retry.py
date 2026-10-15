"""Retries happen in the transport: 429 waits, 5xx and connection failures back off."""

from __future__ import annotations

import io

import httpx
import pytest

import grepvine
from grepvine.models import CreateIndexRequest, DeleteObjectsRequest, File
from tests.conftest import Clock, Flavor, Service, connect, error, index_json

pytestmark = pytest.mark.anyio


def ok() -> httpx.Response:
    return httpx.Response(200, json=index_json())


async def test_429_waits_for_retry_after(fx: Flavor, service: Service, clock: Clock) -> None:
    service.reply(
        error(429, "rate_limited", **{"Retry-After": "3"}), error(429, "rate_limited"), ok()
    )
    assert (await fx.run(fx.client.indexes.get("acme", "docs"))).name == "docs"
    # The second answer has no Retry-After and waits the policy's default.
    assert clock.sleeps == [3.0, 1.0]


async def test_429_wait_is_bounded_and_jittered(kind: str, service: Service, clock: Clock) -> None:
    policy = grepvine.RetryPolicy(max_retry_after=10, retry_after_jitter=0.2)
    service.reply(error(429, "rate_limited", **{"Retry-After": "120"}), ok())
    async with connect(kind, service, retry=policy) as fx:
        await fx.run(fx.client.indexes.get("acme", "docs"))
    [wait] = clock.sleeps
    assert 8.0 <= wait <= 12.0


async def test_429_gives_up_after_the_wait_budget(
    kind: str, service: Service, clock: Clock
) -> None:
    policy = grepvine.RetryPolicy(retry_after_jitter=0, max_throttled_wait=10)
    service.route = lambda request: error(429, "rate_limited", **{"Retry-After": "4"})
    async with connect(kind, service, retry=policy) as fx:
        with pytest.raises(grepvine.RateLimitedError):
            await fx.run(fx.client.indexes.get("acme", "docs"))
    assert clock.sleeps == [4.0, 4.0]
    assert len(service.requests) == 3


async def test_5xx_backs_off_then_succeeds(fx: Flavor, service: Service, clock: Clock) -> None:
    service.reply(error(503, "unavailable"), error(500, "internal"), ok())
    await fx.run(fx.client.indexes.get("acme", "docs"))
    assert clock.sleeps == [0.1, 0.2]


async def test_5xx_on_every_attempt(fx: Flavor, service: Service, clock: Clock) -> None:
    service.route = lambda request: error(503, "unavailable")
    with pytest.raises(grepvine.ServerError):
        await fx.run(fx.client.indexes.get("acme", "docs"))
    assert len(service.requests) == 3
    assert clock.sleeps == [0.1, 0.2]


async def test_connection_failures_back_off(fx: Flavor, service: Service, clock: Clock) -> None:
    service.reply(httpx.ConnectError("refused"), ok())
    await fx.run(fx.client.indexes.get("acme", "docs"))
    assert clock.sleeps == [0.1]


async def test_connection_failures_become_transport_error(fx: Flavor, service: Service) -> None:
    service.reply(*[httpx.ReadTimeout("slow")] * 3)
    with pytest.raises(grepvine.TransportError) as raised:
        await fx.run(fx.client.indexes.get("acme", "docs"))
    assert isinstance(raised.value.__cause__, httpx.ReadTimeout)
    assert len(service.requests) == 3


async def test_4xx_is_not_retried(fx: Flavor, service: Service, clock: Clock) -> None:
    service.reply(error(404, "not_found"))
    with pytest.raises(grepvine.NotFoundError):
        await fx.run(fx.client.indexes.get("acme", "docs"))
    assert clock.sleeps == [] and len(service.requests) == 1


async def test_writes_keep_one_idempotency_key_across_retries(fx: Flavor, service: Service) -> None:
    service.reply(
        error(503, "unavailable"),
        error(429, "rate_limited"),
        httpx.Response(201, json=index_json()),
    )
    await fx.run(fx.client.indexes.create("acme", body=CreateIndexRequest(name="docs")))
    keys = {request.headers["Idempotency-Key"] for request in service.requests}
    assert len(service.requests) == 3 and len(keys) == 1
    assert len(keys.pop()) >= 16


async def test_each_write_gets_its_own_key(fx: Flavor, service: Service) -> None:
    service.route = lambda request: httpx.Response(200, json={"results": []})
    body = DeleteObjectsRequest(objects=[])
    await fx.run(fx.client.documents.delete_batch("acme", "docs", body=body))
    await fx.run(fx.client.documents.delete_batch("acme", "docs", body=body))
    first, second = (request.headers["Idempotency-Key"] for request in service.requests)
    assert first != second


async def test_a_given_idempotency_key_is_kept(fx: Flavor, service: Service) -> None:
    service.reply(error(500, "internal"), httpx.Response(200, json={"results": []}))
    body = File(payload=io.BytesIO(b""))
    await fx.run(fx.client.documents.put_batch("acme", "docs", body=body, idempotency_key="k" * 16))
    assert [request.headers["Idempotency-Key"] for request in service.requests] == ["k" * 16] * 2


async def test_reads_carry_no_idempotency_key(fx: Flavor, service: Service) -> None:
    service.reply(ok())
    await fx.run(fx.client.indexes.get("acme", "docs"))
    assert "Idempotency-Key" not in service.requests[0].headers


def test_policy_validation() -> None:
    with pytest.raises(ValueError):
        grepvine.RetryPolicy(max_attempts=0)
    with pytest.raises(ValueError):
        grepvine.RetryPolicy(retry_after_jitter=1.0)
