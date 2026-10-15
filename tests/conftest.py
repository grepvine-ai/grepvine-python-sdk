"""Shared fixtures: the fake service and a client of either flavour."""

from __future__ import annotations

import inspect
from collections.abc import AsyncIterator, Iterable
from typing import Any

import httpx
import pytest

from grepvine_sdk import AsyncClient, Client
from tests.fake_server import API_KEY, FakeGrepvine

ENDPOINT = "http://grepvine.test"


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
def fake() -> FakeGrepvine:
    return FakeGrepvine()


def no_sleep(seconds: float) -> None:
    """A sleep that returns at once; tests inspect the requested durations instead."""


async def no_async_sleep(seconds: float) -> None:
    """The asynchronous twin of :func:`no_sleep`."""


@pytest.fixture
def client(fake: FakeGrepvine) -> Iterable[Client]:
    with Client(
        api_key=API_KEY, endpoint=ENDPOINT, transport=httpx.MockTransport(fake.handle), env={}
    ) as sync_client:
        sync_client._sleep = no_sleep
        yield sync_client


class Flavor:
    """Lets one test body drive either client.

    ``run`` awaits a value when it is awaitable and returns it otherwise;
    ``collect`` drains a synchronous or asynchronous iterable into a list.
    """

    def __init__(self, client: Client | AsyncClient, name: str) -> None:
        self.client = client
        self.name = name
        self.is_async = name == "async"

    async def run(self, value: Any) -> Any:
        if inspect.isawaitable(value):
            return await value
        return value

    async def collect(self, iterable: Any) -> list[Any]:
        if self.is_async:
            return [item async for item in iterable]
        return list(iterable)


@pytest.fixture(params=["sync", "async"])
async def fx(request: pytest.FixtureRequest, fake: FakeGrepvine) -> AsyncIterator[Flavor]:
    transport = httpx.MockTransport(fake.handle)
    kwargs: dict[str, Any] = {"api_key": API_KEY, "endpoint": ENDPOINT, "env": {}}
    if request.param == "sync":
        with Client(transport=transport, **kwargs) as sync_client:
            sync_client._sleep = no_sleep
            yield Flavor(sync_client, "sync")
    else:
        async with AsyncClient(transport=transport, **kwargs) as async_client:
            async_client._sleep = no_async_sleep
            yield Flavor(async_client, "async")
