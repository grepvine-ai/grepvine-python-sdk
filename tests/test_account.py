from __future__ import annotations

from typing import Any

import httpx
import pytest

from grepvine import (
    AsyncClient,
    AuthenticationError,
    Client,
    ConfigurationError,
    ConflictError,
    PermissionDeniedError,
    User,
)
from tests.conftest import ENDPOINT, Flavor, no_async_sleep, no_sleep
from tests.fake_accounts import SESSION_COOKIE
from tests.fake_server import FakeGrepvine

pytestmark = pytest.mark.anyio


@pytest.fixture(params=["sync", "async"])
async def anonymous(request: pytest.FixtureRequest, fake: FakeGrepvine) -> Any:
    """A client with no API key, as a script that signs in would have."""
    transport = httpx.MockTransport(fake.handle)
    kwargs: dict[str, Any] = {"endpoint": ENDPOINT}
    if request.param == "sync":
        with Client(transport=transport, **kwargs) as sync_client:
            sync_client._sleep = no_sleep
            yield Flavor(sync_client, "sync")
    else:
        async with AsyncClient(transport=transport, **kwargs) as async_client:
            async_client._sleep = no_async_sleep
            yield Flavor(async_client, "async")


def _csrf(fx: Flavor) -> str:
    session = fx.client._state.session
    assert session is not None
    return session.csrf_token


async def test_register_starts_a_session_used_by_later_requests(
    anonymous: Flavor, fake: FakeGrepvine
) -> None:
    fx = anonymous
    with pytest.raises(ConfigurationError, match="no API key"):
        await fx.run(fx.client.account.me())
    assert await fx.run(fx.client.account.username_available("bob-smith"))

    user = await fx.run(
        fx.client.account.register("bob-smith", "bob@example.com", "a long password")
    )

    assert isinstance(user, User)
    assert (user.name, user.email) == ("bob-smith", "bob@example.com")
    assert not await fx.run(fx.client.account.username_available("Bob-Smith"))
    assert (await fx.run(fx.client.account.me())).name == "bob-smith"
    request = fake.requests[-1]
    assert "authorization" not in request.headers
    assert request.headers["cookie"].startswith(f"{SESSION_COOKIE}=")
    with pytest.raises(ConflictError) as excinfo:
        await fx.run(fx.client.account.register("bob-smith", "b@example.com", "a long password"))
    assert excinfo.value.code == "username_taken"


async def test_login_sends_the_csrf_token_and_follows_its_rotation(
    anonymous: Flavor, fake: FakeGrepvine
) -> None:
    fx = anonymous
    with pytest.raises(AuthenticationError):
        await fx.run(fx.client.account.login("alice", "wrong"))

    user = await fx.run(fx.client.account.login("alice@example.com", "correct horse battery"))
    assert user.name == "alice"
    first_token = _csrf(fx)

    # Reading the current user issues a new CSRF token; the next state change must carry it.
    await fx.run(fx.client.account.me())
    assert _csrf(fx) != first_token
    created = await fx.run(fx.client.organizations.create("acme"))
    assert created.name == "acme"
    assert fake.requests[-1].headers["x-csrf-token"] == _csrf(fx)

    await fx.run(fx.client.account.change_password("correct horse battery", "a newer password"))
    assert fake.accounts.users["alice"].password == "a newer password"
    with pytest.raises(AuthenticationError):
        await fx.run(fx.client.account.change_password("wrong", "another password"))

    await fx.run(fx.client.account.logout())
    assert fx.client._state.session is None
    assert fake.accounts.sessions == {}
    with pytest.raises(ConfigurationError):
        await fx.run(fx.client.account.me())


async def test_a_stale_csrf_token_is_refused(anonymous: Flavor, fake: FakeGrepvine) -> None:
    fx = anonymous
    await fx.run(fx.client.account.login("alice", "correct horse battery"))
    cookie = next(iter(fake.accounts.sessions))
    fake.accounts.sessions[cookie] = ("alice", "rotated-elsewhere-0000")
    with pytest.raises(PermissionDeniedError):
        await fx.run(fx.client.organizations.create("acme"))


async def test_a_session_replaces_the_api_key_until_logout(fx: Flavor, fake: FakeGrepvine) -> None:
    await fx.run(fx.client.account.login("alice", "correct horse battery"))
    await fx.run(fx.client.account.me())
    assert "authorization" not in fake.requests[-1].headers

    await fx.run(fx.client.account.logout())
    await fx.run(fx.client.account.me())
    assert fake.requests[-1].headers["authorization"].startswith("Bearer ")
    assert "cookie" not in fake.requests[-1].headers


async def test_development_session_cookie_is_accepted(fx: Flavor) -> None:
    from grepvine._core.ops import _session

    response = httpx.Response(
        200,
        headers=[
            ("Set-Cookie", "other=1; Path=/"),
            ("Set-Cookie", "grepvine-session=abc; Path=/; HttpOnly"),
            ("X-Csrf-Token", "token-0123456789abcdef"),
        ],
    )
    session = _session(response)
    assert session is not None
    assert (session.cookie_name, session.cookie) == ("grepvine-session", "abc")
    assert _session(httpx.Response(200, headers={"X-Csrf-Token": "t"})) is None
