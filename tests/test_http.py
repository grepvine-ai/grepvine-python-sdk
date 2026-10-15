"""``client.http``: an HTTPX client with the client's endpoint, credentials and retries."""

from __future__ import annotations

import httpx
import pytest

from grepvine import Client
from tests.conftest import ENDPOINT, Flavor
from tests.fake_server import API_KEY, FakeGrepvine

pytestmark = pytest.mark.anyio


async def test_http_sends_authenticated_requests_relative_to_the_endpoint(
    fx: Flavor, fake: FakeGrepvine
) -> None:
    fake.add_organization("acme")
    http = fx.client.http
    assert isinstance(http, httpx.AsyncClient if fx.is_async else httpx.Client)
    assert str(http.base_url) == f"{ENDPOINT}/v1/"

    response = await fx.run(http.get("/organizations/acme"))

    assert response.status_code == 200
    assert response.json()["name"] == "acme"
    request = fake.requests[-1]
    assert request.headers["authorization"] == f"Bearer {API_KEY}"
    assert request.headers["user-agent"].startswith("grepvine-python-sdk/")


async def test_http_retries_but_returns_errors_as_they_are(fx: Flavor, fake: FakeGrepvine) -> None:
    fake.add_organization("acme")
    fake.fail_next(503)
    response = await fx.run(fx.client.http.get("/organizations/acme"))
    assert response.status_code == 200
    assert len(fake.requests) == 2

    missing = await fx.run(fx.client.http.get("/organizations/nope"))
    assert missing.status_code == 404
    assert missing.json()["code"] == "not_found"


def test_http_follows_reconfiguration(fake: FakeGrepvine) -> None:
    client = Client(
        api_key="gvk_old-0000000000000000",
        endpoint="http://one.test",
        transport=httpx.MockTransport(fake.handle),
    )
    first = client.http
    assert client.http is first
    client.configure(endpoint="http://two.test", api_key=API_KEY)
    second = client.http
    assert second is not first
    assert str(second.base_url) == "http://two.test/v1/"
    assert second.headers["authorization"] == f"Bearer {API_KEY}"
    client.close()
    with pytest.raises(RuntimeError, match="closed"):
        client.http  # noqa: B018 - reading it is the point


def test_responses_the_sdk_cannot_read_raise_grepvine_errors(fake: FakeGrepvine) -> None:
    from grepvine import GrepvineError

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"unexpected": True})

    client = Client(api_key=API_KEY, endpoint=ENDPOINT, transport=httpx.MockTransport(handler))
    with pytest.raises(GrepvineError, match="cannot read"):
        client.organizations.get("acme")
