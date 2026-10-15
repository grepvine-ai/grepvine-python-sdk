"""Client options, authentication headers, the session after login, and closing."""

from __future__ import annotations

import httpx
import pytest

import grepvine
from grepvine.models import DeviceDecisionRequest, LoginRequest
from tests.conftest import API_KEY, Flavor, Service, index_json

pytestmark = pytest.mark.anyio


async def test_bearer_key_user_agent_and_default_endpoint(fx: Flavor, service: Service) -> None:
    service.reply(httpx.Response(200, json=index_json()))
    index = await fx.run(fx.client.indexes.get("acme", "docs"))
    assert isinstance(index, grepvine.models.Index) and index.name == "docs"
    request = service.requests[0]
    assert str(request.url) == "https://api.grepvine.ai/v1/organizations/acme/indexes/docs"
    assert request.headers["Authorization"] == f"Bearer {API_KEY}"
    assert request.headers["User-Agent"].startswith(f"grepvine-python/{grepvine.__version__} ")


@pytest.mark.parametrize(
    ("endpoint", "url"),
    [
        ("https://grepvine.example.com", "https://grepvine.example.com/v1/organizations"),
        ("https://grepvine.example.com/", "https://grepvine.example.com/v1/organizations"),
        ("http://localhost:8080/v1", "http://localhost:8080/v1/organizations"),
        ("http://localhost:8080/v1/", "http://localhost:8080/v1/organizations"),
    ],
)
def test_endpoint_gets_v1_once(endpoint: str, url: str, service: Service) -> None:
    service.reply(
        httpx.Response(
            200, json={"results": [], "pagination": {"next_page_id": "", "has_next": False}}
        )
    )
    with grepvine.Client(
        endpoint=endpoint, transport=httpx.MockTransport(service.handle)
    ) as client:
        client.organizations.list()
    assert str(service.requests[0].url).split("?")[0] == url
    assert "Authorization" not in service.requests[0].headers


def test_endpoint_must_be_a_url() -> None:
    with pytest.raises(grepvine.ConfigurationError):
        grepvine.Client(endpoint="api.grepvine.ai")


def test_reads_no_environment(monkeypatch: pytest.MonkeyPatch, service: Service) -> None:
    monkeypatch.setenv("GREPVINE_API_KEY", "from-env")
    monkeypatch.setenv("GREPVINE_API_ENDPOINT", "https://env.example.com")
    service.reply(httpx.Response(200, json=index_json()))
    with grepvine.Client(transport=httpx.MockTransport(service.handle)) as client:
        client.indexes.get("acme", "docs")
    assert service.requests[0].url.host == "api.grepvine.ai"
    assert "Authorization" not in service.requests[0].headers


async def test_login_session_carries_cookie_and_csrf(fx: Flavor, service: Service) -> None:
    user = {
        "id": "00000000-0000-0000-0000-000000000002",
        "name": "alice",
        "email": "a@example.com",
        "created_at": "2026-01-01T00:00:00Z",
    }
    service.reply(
        httpx.Response(
            200,
            json=user,
            headers={
                "Set-Cookie": "__Host-grepvine-session=s3cret; Path=/; Secure; HttpOnly",
                "X-Csrf-Token": "csrf-1",
            },
        ),
        httpx.Response(204),
    )
    signed_in = await fx.run(
        fx.client.account.login(body=LoginRequest(identifier="alice", password="pw"))
    )
    assert signed_in.name == "alice"
    assert (
        await fx.run(fx.client.device_login.approve(body=DeviceDecisionRequest(user_code="ABCD")))
        is None
    )
    approve = service.requests[1]
    assert approve.headers["X-Csrf-Token"] == "csrf-1"
    assert "__Host-grepvine-session=s3cret" in approve.headers["Cookie"]


def test_context_manager_closes(service: Service) -> None:
    with grepvine.Client(transport=httpx.MockTransport(service.handle)) as client:
        pass
    assert client.http.is_closed


async def test_async_context_manager_closes(service: Service) -> None:
    async with grepvine.AsyncClient(transport=httpx.MockTransport(service.handle)) as client:
        pass
    assert client.http.is_closed


def test_empty_answers_are_accepted(service: Service) -> None:
    service.reply(httpx.Response(202))
    with grepvine.Client(transport=httpx.MockTransport(service.handle)) as client:
        client.indexes.delete("acme", "docs")
    assert service.requests[0].method == "DELETE"
