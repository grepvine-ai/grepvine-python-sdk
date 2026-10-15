"""device_login.authorize reports the code and polls at the service's interval."""

from __future__ import annotations

import httpx
import pytest

import grepvine
from grepvine.models import APIKeyCreated, DeviceAuthorization
from tests.conftest import Clock, Flavor, Service, error

pytestmark = pytest.mark.anyio
AUTHORIZATION = {
    "device_code": "dev-1",
    "user_code": "ABCD-EFGH",
    "verification_uri": "https://grepvine.ai/device",
    "verification_uri_complete": "https://grepvine.ai/device?code=ABCD-EFGH",
    "expires_in": 600,
    "interval": 5,
}
KEY = {
    "id": "00000000-0000-0000-0000-000000000003",
    "name": "laptop",
    "prefix": "gvk_ab",
    "created_at": "2026-01-01T00:00:00Z",
    "key": "gvk_abcdef",
}


async def test_polls_until_issued_and_slows_down(
    fx: Flavor, service: Service, clock: Clock
) -> None:
    service.reply(
        httpx.Response(200, json=AUTHORIZATION),
        error(400, "authorization_pending"),
        error(400, "slow_down"),
        error(400, "authorization_pending"),
        httpx.Response(200, json=KEY),
    )
    shown: list[DeviceAuthorization] = []
    key = await fx.run(fx.client.device_login.authorize("laptop", on_code=shown.append))
    assert isinstance(key, APIKeyCreated) and key.key == "gvk_abcdef"
    assert [code.user_code for code in shown] == ["ABCD-EFGH"]
    assert clock.sleeps == [5, 5, 10, 10]
    assert service.json(0) == {"api_key_name": "laptop"}
    assert service.json(1) == {"device_code": "dev-1"}


async def test_denied(fx: Flavor, service: Service) -> None:
    service.reply(httpx.Response(200, json=AUTHORIZATION), error(400, "access_denied"))
    with pytest.raises(grepvine.InvalidRequestError) as raised:
        await fx.run(fx.client.device_login.authorize("laptop", on_code=lambda code: None))
    assert raised.value.code == "access_denied"


async def test_times_out(fx: Flavor, service: Service, clock: Clock) -> None:
    service.reply(httpx.Response(200, json=AUTHORIZATION))
    service.route = lambda request: error(400, "authorization_pending")
    with pytest.raises(TimeoutError):
        await fx.run(
            fx.client.device_login.authorize("laptop", on_code=lambda code: None, timeout=12)
        )
    assert clock.sleeps == [5, 5]


async def test_stops_when_the_code_expires(fx: Flavor, service: Service, clock: Clock) -> None:
    service.reply(httpx.Response(200, json={**AUTHORIZATION, "expires_in": 7}))
    service.route = lambda request: error(400, "authorization_pending")
    with pytest.raises(TimeoutError):
        await fx.run(fx.client.device_login.authorize("laptop", on_code=lambda code: None))
    assert clock.sleeps == [5]
