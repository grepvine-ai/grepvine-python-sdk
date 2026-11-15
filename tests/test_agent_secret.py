"""An agent secret is exchanged for a token, renewed before it expires, and never sent elsewhere."""

from __future__ import annotations

import asyncio
import threading
import time
from pathlib import Path
from urllib.parse import parse_qs

import httpx
import pytest

import grepvine
from tests.conftest import Clock, Service, connect, error, index_json

pytestmark = pytest.mark.anyio
SECRET = "gvs_0123456789abcdefghij"


class Agent:
    """A service that exchanges SECRET for numbered tokens and answers index requests."""

    def __init__(self, delay: float = 0.0) -> None:
        self.service = Service()
        self.service.route = self.route
        self.tokens = 0
        self.delay = delay
        self.refuse: str | None = None

    def route(self, request: httpx.Request) -> httpx.Response:
        if request.url.path == "/oauth/token":
            form = parse_qs(request.content.decode())
            assert form == {"grant_type": ["client_credentials"], "client_secret": [SECRET]}
            time.sleep(self.delay)
            self.tokens += 1
            return httpx.Response(
                200,
                json={
                    "access_token": f"gvt_{self.tokens}",
                    "token_type": "Bearer",
                    "expires_in": 900,
                    "scope": "search read",
                },
            )
        if request.headers.get("Authorization") == self.refuse:
            return error(401, "unauthenticated")
        return httpx.Response(200, json=index_json())

    def bearers(self) -> list[str | None]:
        """The token each index request carried; the secret never leaves the token endpoint."""
        data = [r for r in self.service.requests if r.url.path != "/oauth/token"]
        for request in data:
            assert SECRET not in str(request.headers) + request.content.decode() + str(request.url)
        return [r.headers.get("Authorization") for r in data]


async def get(fx: object) -> None:
    await fx.run(fx.client.indexes.get(organization="acme", index="docs"))  # type: ignore[attr-defined]


async def test_exchanges_once_and_renews_before_expiry(kind: str, clock: Clock) -> None:
    agent = Agent()
    async with connect(kind, agent.service, api_key=None, agent_secret=SECRET) as fx:
        await get(fx)
        await get(fx)
        clock.now += 839
        await get(fx)
        clock.now += 1
        await get(fx)
    token = agent.service.requests[0]
    assert str(token.url) == "https://api.grepvine.ai/oauth/token"
    assert "Authorization" not in token.headers
    assert agent.tokens == 2
    assert agent.bearers() == ["Bearer gvt_1"] * 3 + ["Bearer gvt_2"]


async def test_a_refused_token_is_exchanged_again(kind: str) -> None:
    agent = Agent()
    async with connect(kind, agent.service, api_key=None, agent_secret=SECRET) as fx:
        await get(fx)
        agent.refuse = "Bearer gvt_1"
        with pytest.raises(grepvine.AuthenticationError):
            await get(fx)
        await get(fx)
    assert agent.bearers() == ["Bearer gvt_1", "Bearer gvt_1", "Bearer gvt_2"]


async def test_an_invalid_secret_is_an_authentication_error() -> None:
    service = Service()
    body = {"error": "invalid_client", "error_description": "the agent secret is not valid"}
    service.reply(httpx.Response(401, json=body))
    async with connect("sync", service, api_key=None, agent_secret=SECRET) as fx:
        with pytest.raises(grepvine.AuthenticationError) as caught:
            await get(fx)
    assert (caught.value.code, caught.value.message) == (
        "invalid_client",
        "the agent secret is not valid",
    )


async def test_threads_share_one_exchange() -> None:
    agent = Agent(delay=0.05)
    async with connect("sync", agent.service, api_key=None, agent_secret=SECRET) as fx:
        threads = [
            threading.Thread(target=fx.client.indexes.get, args=("acme", "docs")) for _ in range(8)
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
    assert agent.tokens == 1
    assert agent.bearers() == ["Bearer gvt_1"] * 8


async def test_tasks_share_one_exchange() -> None:
    agent = Agent()

    async def handle(request: httpx.Request) -> httpx.Response:
        await asyncio.sleep(0.01)
        return agent.service.handle(request)

    async with grepvine.AsyncClient(
        agent_secret=SECRET, trust_env=False, transport=httpx.MockTransport(handle)
    ) as client:
        await asyncio.gather(*(client.indexes.get("acme", "docs") for _ in range(8)))
    assert agent.tokens == 1
    assert agent.bearers() == ["Bearer gvt_1"] * 8


def test_environment_secret_wins_over_a_file_key(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = tmp_path / ".grepvine/config.yaml"
    config.parent.mkdir()
    config.write_text("api_key: gvk_file\n")
    config.chmod(0o600)
    monkeypatch.setenv("GREPVINE_AGENT_SECRET", SECRET)
    settings = grepvine.Client().settings
    assert (settings.api_key, settings.agent_secret) == (None, SECRET)
    assert SECRET not in repr(settings) and "gvs_0123****" in repr(settings)


def test_one_source_with_both_is_an_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(grepvine.ConfigurationError, match="not both"):
        grepvine.Client(api_key="gvk_x", agent_secret=SECRET)
    config = tmp_path / "both.yaml"
    config.write_text(f"api_key: gvk_file\nagent_secret: {SECRET}\n")
    config.chmod(0o600)
    with pytest.raises(grepvine.ConfigurationError, match="not both"):
        grepvine.Client.from_config(config)
    config.chmod(0o644)
    with pytest.raises(grepvine.ConfigurationError, match="chmod 600"):
        grepvine.Client.from_config(config)
