from __future__ import annotations

import json

import pytest

from grepvine import APIKeyCreated, DeviceAuthorization, InvalidRequestError, NotFoundError
from tests.conftest import Flavor
from tests.fake_server import FakeGrepvine

pytestmark = pytest.mark.anyio


def _record_sleeps(fx: Flavor, clock: list[float]) -> list[float]:
    """Make sleeping advance the fake clock, and record every sleep."""
    sleeps: list[float] = []

    def advance(seconds: float) -> None:
        sleeps.append(seconds)
        clock[0] += seconds

    async def advance_async(seconds: float) -> None:
        advance(seconds)

    fx.client._sleep = advance_async if fx.is_async else advance
    fx.client._clock = lambda: clock[0]
    return sleeps


async def test_start_poll_approve(fx: Flavor, fake: FakeGrepvine) -> None:
    authorization = await fx.run(fx.client.device_login.start("laptop"))
    assert isinstance(authorization, DeviceAuthorization)
    assert authorization.interval == 5
    assert authorization.verification_uri_complete.endswith(authorization.user_code)
    assert authorization.device_code not in repr(authorization)

    assert await fx.run(fx.client.device_login.poll(authorization.device_code)) is None

    await fx.run(fx.client.device_login.approve(authorization.user_code))
    assert json.loads(fake.requests[-1].content) == {"user_code": authorization.user_code}
    key = await fx.run(fx.client.device_login.poll(authorization.device_code))
    assert isinstance(key, APIKeyCreated)
    assert key.name == "laptop"
    with pytest.raises(InvalidRequestError) as excinfo:
        await fx.run(fx.client.device_login.poll(authorization.device_code))
    assert excinfo.value.code == "expired_token"
    with pytest.raises(NotFoundError):
        await fx.run(fx.client.device_login.approve(authorization.user_code))


async def test_deny(fx: Flavor, fake: FakeGrepvine) -> None:
    authorization = await fx.run(fx.client.device_login.start("laptop"))
    await fx.run(fx.client.device_login.deny(authorization.user_code))
    with pytest.raises(InvalidRequestError) as excinfo:
        await fx.run(fx.client.device_login.poll(authorization.device_code))
    assert excinfo.value.code == "access_denied"


async def test_authorize_polls_at_the_interval_until_approved(
    fx: Flavor, fake: FakeGrepvine
) -> None:
    clock = [1000.0]
    sleeps = _record_sleeps(fx, clock)
    shown: list[DeviceAuthorization] = []
    fake.accounts.slow_down_polls = 1

    def on_code(authorization: DeviceAuthorization) -> None:
        shown.append(authorization)

    def approve_on_third_poll(polls: int) -> None:
        if polls == 3:
            device = fake.accounts.device(shown[0].user_code)
            device.status, device.user = "approved", "alice"

    fake.accounts.on_poll = approve_on_third_poll

    key = await fx.run(fx.client.device_login.authorize("laptop", on_code=on_code, timeout=120))

    assert key.name == "laptop"
    assert [a.user_code for a in shown] == [fake.accounts.devices[0].user_code]
    # The first poll is told to slow down, so the interval grows by five seconds.
    assert sleeps == [5.0, 10.0, 10.0]


async def test_authorize_accepts_a_coroutine_callback(fx: Flavor, fake: FakeGrepvine) -> None:
    if not fx.is_async:
        pytest.skip("only an asynchronous client awaits its callback")
    _record_sleeps(fx, [0.0])
    seen: list[str] = []

    async def on_code(authorization: DeviceAuthorization) -> None:
        seen.append(authorization.user_code)
        device = fake.accounts.device(authorization.user_code)
        device.status, device.user = "approved", "alice"

    key = await fx.run(fx.client.device_login.authorize("laptop", on_code=on_code))
    assert seen
    assert key.name == "laptop"


async def test_authorize_raises_when_denied(fx: Flavor, fake: FakeGrepvine) -> None:
    _record_sleeps(fx, [0.0])

    def deny(authorization: DeviceAuthorization) -> None:
        fake.accounts.device(authorization.user_code).status = "denied"

    with pytest.raises(InvalidRequestError) as excinfo:
        await fx.run(fx.client.device_login.authorize("laptop", on_code=deny))
    assert excinfo.value.code == "access_denied"


async def test_authorize_times_out(fx: Flavor, fake: FakeGrepvine) -> None:
    clock = [0.0]
    sleeps = _record_sleeps(fx, clock)
    with pytest.raises(TimeoutError):
        await fx.run(fx.client.device_login.authorize("laptop", on_code=lambda _: None, timeout=12))
    assert sleeps == [5.0, 5.0]

    # Without a timeout, the login's own expiry bounds the wait.
    fake.accounts.device_expires_in = 7
    with pytest.raises(TimeoutError):
        await fx.run(fx.client.device_login.authorize("laptop", on_code=lambda _: None))
    with pytest.raises(ValueError, match="positive"):
        await fx.run(fx.client.device_login.authorize("laptop", on_code=print, timeout=0))
