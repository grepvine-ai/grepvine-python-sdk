"""Shared fixtures: a scripted service on httpx.MockTransport, a fake clock, and both clients."""

from __future__ import annotations

import inspect
import json
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from typing import Any

import httpx
import pytest

from grepvine import AsyncClient, Client, RetryPolicy, _retry

Handler = Callable[[httpx.Request], httpx.Response]
API_KEY = "gvk_test"
NO_JITTER = RetryPolicy(retry_after_jitter=0.0)


def index_json(name: str = "docs", state: str = "ready") -> dict[str, Any]:
    return {
        "id": "00000000-0000-0000-0000-000000000001",
        "organization": "acme",
        "name": name,
        "canonical_id": "c",
        "description": "",
        "tags": {},
        "state": state,
        "document_count": 0,
        "content_bytes": 0,
        "created_at": "2026-01-01T00:00:00Z",
    }


def page_json(results: list[Any], next_page_id: str = "") -> dict[str, Any]:
    return {
        "results": results,
        "pagination": {"next_page_id": next_page_id, "has_next": bool(next_page_id)},
    }


def error(status: int, code: str, message: str = "failed", **headers: str) -> httpx.Response:
    body = {"code": code, "reason": "test", "error": message}
    return httpx.Response(status, json=body, headers=headers)


class Service:
    """Answers requests from a queue of handlers or a routing function, and records them."""

    def __init__(self) -> None:
        self.requests: list[httpx.Request] = []
        self.queue: list[httpx.Response | Handler | Exception] = []
        self.route: Handler = lambda request: error(404, "not_found", "no route")

    def reply(self, *answers: httpx.Response | Handler | Exception) -> None:
        self.queue.extend(answers)

    def handle(self, request: httpx.Request) -> httpx.Response:
        request.read()
        self.requests.append(request)
        answer = self.queue.pop(0) if self.queue else self.route
        if isinstance(answer, Exception):
            raise answer
        return answer if isinstance(answer, httpx.Response) else answer(request)

    def json(self, position: int = -1) -> Any:
        return json.loads(self.requests[position].content)


class Clock:
    """Replaces the SDK's clock and sleeps: sleeping advances the time and is recorded."""

    def __init__(self) -> None:
        self.now = 1000.0
        self.sleeps: list[float] = []

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.now += seconds

    async def async_sleep(self, seconds: float) -> None:
        self.sleep(seconds)


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
def service() -> Service:
    return Service()


@pytest.fixture(autouse=True)
def clock(monkeypatch: pytest.MonkeyPatch) -> Clock:
    fake = Clock()
    monkeypatch.setattr(_retry, "sleep", fake.sleep)
    monkeypatch.setattr(_retry, "async_sleep", fake.async_sleep)
    monkeypatch.setattr(_retry, "monotonic", lambda: fake.now)
    return fake


class Flavor:
    """Drives either client from one test body: ``await fx.run(fx.client.indexes.get(...))``."""

    def __init__(self, client: Client | AsyncClient) -> None:
        self.client: Any = client
        self.is_async = isinstance(client, AsyncClient)

    async def run(self, value: Any) -> Any:
        return await value if inspect.isawaitable(value) else value

    async def collect(self, iterable: Any) -> list[Any]:
        return [item async for item in iterable] if self.is_async else list(iterable)


@asynccontextmanager
async def connect(kind: str, service: Service, **options: Any) -> AsyncIterator[Flavor]:
    """Open a client of the given kind on the service; ``options`` override the defaults."""
    options = {"api_key": API_KEY, "retry": NO_JITTER, **options}
    if kind == "sync":
        with Client(transport=httpx.MockTransport(service.handle), **options) as client:
            yield Flavor(client)
    else:
        async with AsyncClient(transport=httpx.MockTransport(service.handle), **options) as aclient:
            yield Flavor(aclient)


@pytest.fixture(params=["sync", "async"])
def kind(request: pytest.FixtureRequest) -> str:
    return str(request.param)


@pytest.fixture
async def fx(kind: str, service: Service) -> AsyncIterator[Flavor]:
    async with connect(kind, service) as flavor:
        yield flavor
