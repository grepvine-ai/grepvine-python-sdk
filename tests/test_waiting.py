"""indexes.wait_until_ready reads the index until it is ready."""

from __future__ import annotations

import httpx
import pytest

import grepvine
from tests.conftest import Clock, Flavor, Service, index_json

pytestmark = pytest.mark.anyio


async def test_waits_while_creating(fx: Flavor, service: Service, clock: Clock) -> None:
    service.reply(
        httpx.Response(200, json=index_json(state="creating")),
        httpx.Response(200, json=index_json(state="creating")),
        httpx.Response(200, json=index_json(state="ready")),
    )
    index = await fx.run(fx.client.indexes.wait_until_ready("acme", "docs", interval=2))
    assert index.state == grepvine.models.IndexState.READY
    assert clock.sleeps == [2, 2]
    assert {request.url.path for request in service.requests} == {
        "/v1/organizations/acme/indexes/docs"
    }


async def test_an_index_being_deleted_never_becomes_ready(fx: Flavor, service: Service) -> None:
    service.reply(httpx.Response(200, json=index_json(state="deleting")))
    with pytest.raises(grepvine.GrepvineError, match="deleting"):
        await fx.run(fx.client.indexes.wait_until_ready("acme", "docs"))


async def test_times_out(fx: Flavor, service: Service, clock: Clock) -> None:
    service.route = lambda request: httpx.Response(200, json=index_json(state="creating"))
    with pytest.raises(TimeoutError):
        await fx.run(fx.client.indexes.wait_until_ready("acme", "docs", timeout=5, interval=1))
    assert sum(clock.sleeps) == 5


async def test_errors_propagate(fx: Flavor, service: Service) -> None:
    service.reply(httpx.Response(404, json={"code": "not_found", "reason": "r", "error": "no"}))
    with pytest.raises(grepvine.NotFoundError):
        await fx.run(fx.client.indexes.wait_until_ready("acme", "docs"))
