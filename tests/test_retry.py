from __future__ import annotations

import random
from concurrent.futures import ThreadPoolExecutor

import httpx
import pytest

from grepvine_sdk import (
    Client,
    PartialBatchError,
    RateLimitedError,
    RetryPolicy,
    ServerError,
    TransportError,
)
from grepvine_sdk._core.retry import (
    BackoffThen,
    Deliver,
    Fail,
    PauseThen,
    decide,
    retry_after_seconds,
)
from grepvine_sdk.errors import APIError, InvalidRequestError, map_error
from grepvine_sdk.models import MutationResult
from tests.conftest import Flavor
from tests.fake_server import API_KEY, FakeGrepvine

pytestmark = pytest.mark.anyio


class ZeroJitter(random.Random):
    def uniform(self, a: float, b: float) -> float:
        return 0.0


def _response(status: int, **headers: str) -> httpx.Response:
    return httpx.Response(status, headers=headers, content=b"{}")


POLICY = RetryPolicy()


def test_retry_after_seconds() -> None:
    rng = ZeroJitter()
    assert retry_after_seconds({}, POLICY, rng) == 1.0
    assert retry_after_seconds({"retry-after": "abc"}, POLICY, rng) == 1.0
    assert retry_after_seconds({"retry-after": "0"}, POLICY, rng) == 1.0
    assert retry_after_seconds({"retry-after": "5"}, POLICY, rng) == 5.0
    assert retry_after_seconds({"retry-after": "999"}, POLICY, rng) == 60.0
    seeded = random.Random(7)
    delays = {retry_after_seconds({"retry-after": "2"}, POLICY, seeded) for _ in range(200)}
    assert all(1.5 <= d <= 2.5 for d in delays)
    assert len(delays) > 1


def test_decide_table() -> None:
    rng = ZeroJitter()
    failure = httpx.ConnectError("boom")
    assert decide(failure, attempt=1, throttled_wait=0, policy=POLICY, rng=rng) == BackoffThen(0.1)
    assert decide(failure, attempt=2, throttled_wait=0, policy=POLICY, rng=rng) == BackoffThen(0.2)
    assert decide(failure, attempt=3, throttled_wait=0, policy=POLICY, rng=rng) == Fail()

    unavailable = _response(503)
    assert decide(unavailable, attempt=1, throttled_wait=0, policy=POLICY, rng=rng) == BackoffThen(
        0.1
    )
    assert decide(unavailable, attempt=3, throttled_wait=0, policy=POLICY, rng=rng) == Deliver()
    assert decide(_response(200), attempt=1, throttled_wait=0, policy=POLICY, rng=rng) == Deliver()
    assert decide(_response(404), attempt=1, throttled_wait=0, policy=POLICY, rng=rng) == Deliver()

    too_many = _response(429, **{"Retry-After": "2"})
    assert decide(too_many, attempt=1, throttled_wait=0, policy=POLICY, rng=rng) == PauseThen(2.0)
    exhausted = decide(too_many, attempt=1, throttled_wait=599, policy=POLICY, rng=rng)
    assert exhausted == Deliver(throttled_wait=599)


def test_policy_validation() -> None:
    with pytest.raises(ValueError, match="max_attempts"):
        RetryPolicy(max_attempts=0)
    with pytest.raises(ValueError, match="jitter"):
        RetryPolicy(retry_after_jitter=1.5)
    assert RetryPolicy(backoff=()).backoff_for(1) == 0.0
    assert RetryPolicy(backoff=(0.5,)).backoff_for(4) == 0.5


def _sleeps(fx: Flavor) -> list[float]:
    recorded: list[float] = []
    if fx.is_async:

        async def asleep(seconds: float) -> None:
            recorded.append(seconds)

        fx.client._sleep = asleep
    else:

        def sleep(seconds: float) -> None:
            recorded.append(seconds)

        fx.client._sleep = sleep
    return recorded


async def test_server_errors_are_retried_with_the_same_idempotency_key(
    fx: Flavor, fake: FakeGrepvine
) -> None:
    fake.add_index("acme/docs")
    sleeps = _sleeps(fx)
    index = await fx.run(fx.client.indexes.get("acme/docs"))
    fake.requests.clear()
    fake.fail_next(503, times=2)

    result = await fx.run(index.documents.put("a.txt", content=b"x"))

    assert isinstance(result, MutationResult)
    assert [request.method for request in fake.requests] == ["PUT", "PUT", "PUT"]
    assert len({request.headers["idempotency-key"] for request in fake.requests}) == 1
    assert sleeps == [0.1, 0.2]


async def test_server_errors_exhaust_attempts(fx: Flavor, fake: FakeGrepvine) -> None:
    fake.add_organization("acme")
    sleeps = _sleeps(fx)
    fake.fail_next(500, times=3)
    with pytest.raises(ServerError) as excinfo:
        await fx.run(fx.client.organizations.get("acme"))
    assert excinfo.value.status_code == 500
    assert len(fake.requests) == 3
    assert sleeps == [0.1, 0.2]


async def test_transport_errors_are_retried(fx: Flavor, fake: FakeGrepvine) -> None:
    fake.add_organization("acme")
    fake.raise_next(httpx.ConnectError("refused"), times=1)
    assert (await fx.run(fx.client.organizations.get("acme"))).name == "acme"
    assert len(fake.requests) == 2

    fake.raise_next(httpx.ReadTimeout("slow"), times=3)
    with pytest.raises(TransportError) as excinfo:
        await fx.run(fx.client.organizations.get("acme"))
    assert isinstance(excinfo.value.__cause__, httpx.ReadTimeout)


async def test_client_errors_are_not_retried(fx: Flavor, fake: FakeGrepvine) -> None:
    fake.add_organization("acme")
    fake.fail_next(400, code="invalid_request", message="bad", times=3)
    with pytest.raises(InvalidRequestError):
        await fx.run(fx.client.organizations.get("acme"))
    assert len(fake.requests) == 1


async def test_429_pauses_every_request_of_the_client(fx: Flavor, fake: FakeGrepvine) -> None:
    fake.add_organization("acme")
    sleeps = _sleeps(fx)
    fx.client._state.rng = ZeroJitter()
    now = [100.0]
    fx.client._clock = lambda: now[0]
    fake.fail_next(429, code="write_backlog", retry_after=2)

    assert (await fx.run(fx.client.organizations.get("acme"))).name == "acme"
    assert sleeps == [2.0]
    assert len(fake.requests) == 2

    # The pause is still in force for the next request until the clock moves on.
    await fx.run(fx.client.organizations.get("acme"))
    assert sleeps == [2.0, 2.0]
    now[0] += 5
    await fx.run(fx.client.organizations.get("acme"))
    assert sleeps == [2.0, 2.0]


async def test_429_without_retry_after_and_budget(fx: Flavor, fake: FakeGrepvine) -> None:
    fake.add_organization("acme")
    sleeps = _sleeps(fx)
    fx.client._state.rng = ZeroJitter()
    fx.client._clock = lambda: 0.0
    fx.client.configure(retry=RetryPolicy(max_throttled_wait=2.5))
    fake.fail_next(429, code="capacity_exhausted", times=3)

    with pytest.raises(RateLimitedError) as excinfo:
        await fx.run(fx.client.organizations.get("acme"))

    assert sleeps == [1.0, 1.0]
    assert excinfo.value.retry_after is None
    assert "slowed down for 2s without success" in str(excinfo.value)
    assert excinfo.value.code == "capacity_exhausted"


async def test_partial_batch_error_wraps_rate_limit(
    fx: Flavor, fake: FakeGrepvine, monkeypatch: pytest.MonkeyPatch
) -> None:
    import grepvine_sdk._core.ops as ops_module

    fake.add_index("acme/docs")
    fake.add_document("acme/docs", "a", "x")
    fake.add_document("acme/docs", "b", "x")
    fx.client._state.rng = ZeroJitter()
    fx.client.configure(retry=RetryPolicy(max_throttled_wait=0.5))
    _sleeps(fx)
    index = await fx.run(fx.client.indexes.get("acme/docs"))
    monkeypatch.setattr(ops_module, "MAX_BATCH_RECORDS", 1)
    fake.fail_next(429, retry_after=1, when=lambda r: b'"b"' in r.content)
    with pytest.raises(PartialBatchError) as excinfo:
        await fx.run(index.documents.delete(["a", "b"]))
    assert isinstance(excinfo.value.__cause__, RateLimitedError)


def test_threads_share_the_pause(fake: FakeGrepvine) -> None:
    fake.add_organization("acme")
    sleeps: list[float] = []
    client = Client(
        api_key=API_KEY,
        endpoint="http://grepvine.test",
        transport=httpx.MockTransport(fake.handle),
        env={},
    )
    client._sleep = sleeps.append
    client._clock = lambda: 0.0
    client._state.throttle.slow(0.0, 5.0)
    with ThreadPoolExecutor(max_workers=4) as pool:
        names = list(pool.map(lambda _: client.organizations.get("acme").name, range(4)))
    assert names == ["acme"] * 4
    assert sleeps == [5.0] * 4


async def test_file_bodies_are_rewound_between_attempts(fx: Flavor, fake: FakeGrepvine) -> None:
    import io

    fake.add_index("acme/docs")
    _sleeps(fx)
    index = await fx.run(fx.client.indexes.get("acme/docs"))
    fake.fail_next(503, times=2, method="PUT")
    body = io.BytesIO(b"prefix|payload")
    body.seek(7)

    await fx.run(index.documents.put("a.txt", content=body))

    assert fake.indexes[("acme", "docs")].documents["a.txt"].content == b"payload"
    assert sum(1 for r in fake.requests if r.method == "PUT") == 3


def test_map_error_parses_bodies() -> None:
    error = map_error(
        httpx.Response(
            412,
            headers={"X-Request-ID": "r9", "Retry-After": "3"},
            content=b'{"code":"precondition_failed","reason":"precondition","error":"nope"}',
        )
    )
    assert (error.status_code, error.code, error.reason, error.message) == (
        412,
        "precondition_failed",
        "precondition",
        "nope",
    )
    assert error.request_id == "r9"
    assert error.retry_after == 3
    assert str(error) == "nope (precondition_failed; request r9)"
    assert "PreconditionFailedError" in repr(error)

    html = map_error(httpx.Response(502, content=b"<html>bad gateway</html>"))
    assert isinstance(html, ServerError)
    assert (html.code, html.message, html.reason) == ("request_failed", "HTTP 502", "http")
    assert str(html) == "HTTP 502 (request_failed)"

    odd = map_error(httpx.Response(302, content=b"[]"))
    assert type(odd) is APIError
    partial = map_error(httpx.Response(400, content=b'{"code":"x"}'))
    assert (partial.code, partial.message, partial.reason) == ("x", "HTTP 400", "http")
