"""Every error answer becomes a typed exception carrying the service's details."""

from __future__ import annotations

import httpx
import pytest

import grepvine
from grepvine.models import CreateIndexRequest
from tests.conftest import Flavor, Service, connect, error

pytestmark = pytest.mark.anyio


@pytest.mark.parametrize(
    ("status", "code", "expected"),
    [
        (400, "invalid_argument", grepvine.InvalidRequestError),
        (400, "invalid_page", grepvine.InvalidPageError),
        (401, "unauthenticated", grepvine.AuthenticationError),
        (403, "permission_denied", grepvine.PermissionDeniedError),
        (404, "not_found", grepvine.NotFoundError),
        (409, "conflict", grepvine.ConflictError),
        (412, "precondition_failed", grepvine.PreconditionFailedError),
        (413, "too_large", grepvine.PayloadTooLargeError),
        (416, "range_not_satisfiable", grepvine.RangeNotSatisfiableError),
        (418, "teapot", grepvine.APIError),
        (503, "unavailable", grepvine.ServerError),
    ],
)
async def test_status_maps_to_error(
    fx: Flavor, service: Service, status: int, code: str, expected: type[grepvine.APIError]
) -> None:
    service.route = lambda request: error(status, code, "it failed", **{"X-Request-Id": "req-1"})
    with pytest.raises(expected) as raised:
        await fx.run(fx.client.indexes.create("acme", body=CreateIndexRequest(name="docs")))
    exc = raised.value
    assert type(exc) is expected
    assert (exc.status_code, exc.code, exc.reason, exc.message) == (
        status,
        code,
        "test",
        "it failed",
    )
    assert exc.request_id == "req-1"
    assert str(exc) == f"it failed ({code}; request req-1)"
    assert isinstance(exc, grepvine.GrepvineError)


async def test_rate_limit_after_waiting_carries_retry_after(kind: str, service: Service) -> None:
    service.reply(error(429, "rate_limited", **{"Retry-After": "7"}))
    async with connect(kind, service, retry=grepvine.RetryPolicy(max_throttled_wait=0)) as fx:
        with pytest.raises(grepvine.RateLimitedError) as raised:
            await fx.run(fx.client.organizations.get("acme"))
    assert raised.value.retry_after == 7


async def test_body_that_is_not_json(kind: str, service: Service) -> None:
    service.reply(httpx.Response(502, text="<html>bad gateway</html>"))
    async with connect(kind, service, retry=grepvine.RetryPolicy(max_attempts=1)) as fx:
        with pytest.raises(grepvine.ServerError) as raised:
            await fx.run(fx.client.organizations.get("acme"))
    assert (raised.value.code, raised.value.message) == ("request_failed", "HTTP 502")
    assert raised.value.request_id is None
