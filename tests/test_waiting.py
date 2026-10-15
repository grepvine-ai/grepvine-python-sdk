from __future__ import annotations

import httpx
import pytest

from grepvine_sdk import AsyncIndex, GrepvineError, Index
from tests.conftest import Flavor
from tests.fake_server import FakeGrepvine

pytestmark = pytest.mark.anyio


def _clock(fx: Flavor) -> list[float]:
    """Make sleeping advance a fake clock and return the recorded sleeps."""
    now = [0.0]
    sleeps: list[float] = []

    def advance(seconds: float) -> None:
        sleeps.append(seconds)
        now[0] += seconds

    async def advance_async(seconds: float) -> None:
        advance(seconds)

    fx.client._sleep = advance_async if fx.is_async else advance
    fx.client._clock = lambda: now[0]
    return sleeps


def _ready_after(fake: FakeGrepvine, reads: int) -> None:
    """Mark every index ready once it has been read ``reads`` times."""
    seen = [0]

    def on_request(request: httpx.Request) -> None:
        if request.method == "GET" and "/indexes/" in request.url.path:
            seen[0] += 1
            if seen[0] >= reads:
                for index in fake.indexes.values():
                    index.state = "ready"

    fake.on_request = on_request


async def test_wait_until_ready_polls_until_the_state_changes(
    fx: Flavor, fake: FakeGrepvine
) -> None:
    sleeps = _clock(fx)
    fake.add_index("acme/docs", state="creating")
    index = await fx.run(fx.client.indexes.get("acme/docs"))
    assert index.state == "creating"
    _ready_after(fake, 3)

    ready = await fx.run(index.wait_until_ready(interval=2))

    assert isinstance(ready, AsyncIndex if fx.is_async else Index)
    assert ready.state == "ready"
    assert index.state == "creating"
    assert sleeps == [2, 2]


async def test_create_with_wait_returns_a_ready_index(fx: Flavor, fake: FakeGrepvine) -> None:
    sleeps = _clock(fx)
    fake.add_organization("acme")
    original = fake._create_index

    def create_creating(request: httpx.Request, organization: str) -> httpx.Response:
        response = original(request, organization)
        for index in fake.indexes.values():
            index.state = "creating"
        return httpx.Response(201, json=next(iter(fake.indexes.values())).to_json())

    fake._create_index = create_creating  # type: ignore[method-assign]
    _ready_after(fake, 2)

    index = await fx.run(fx.client.indexes.create("acme/docs", wait=True))

    assert index.state == "ready"
    assert sleeps == [1.0]
    assert [r.method for r in fake.requests] == ["POST", "GET", "GET"]


async def test_wait_until_ready_times_out(fx: Flavor, fake: FakeGrepvine) -> None:
    sleeps = _clock(fx)
    fake.add_index("acme/docs", state="creating")
    index = await fx.run(fx.client.indexes.get("acme/docs"))
    with pytest.raises(TimeoutError, match="within 5 seconds"):
        await fx.run(index.wait_until_ready(timeout=5, interval=2))
    assert sleeps == [2, 2]
    with pytest.raises(ValueError, match="timeout"):
        await fx.run(index.wait_until_ready(timeout=0))
    with pytest.raises(ValueError, match="interval"):
        await fx.run(index.wait_until_ready(interval=0))


async def test_wait_until_ready_gives_up_on_a_deleting_index(
    fx: Flavor, fake: FakeGrepvine
) -> None:
    _clock(fx)
    fake.add_index("acme/docs", state="deleting")
    index = await fx.run(fx.client.indexes.get("acme/docs"))
    with pytest.raises(GrepvineError, match="acme/docs is deleting"):
        await fx.run(index.wait_until_ready())
