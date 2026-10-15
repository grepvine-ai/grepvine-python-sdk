"""Glue between the operations and httpx, shared by the synchronous and asynchronous clients."""

from __future__ import annotations

import os
import random
import threading
import uuid
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Final

import httpx

from grepvine_sdk._core.config import NOT_LOGGED_IN_MESSAGE, resolve_credentials
from grepvine_sdk._core.effects import Session
from grepvine_sdk._core.retry import BackoffThen, Deliver, Fail, PauseThen, RetryPolicy, decide
from grepvine_sdk._version import __version__
from grepvine_sdk.errors import ConfigurationError, map_error


class _Unset:
    """Marks a keyword argument that was not given."""

    def __repr__(self) -> str:
        return "UNSET"

    def __bool__(self) -> bool:
        return False


UNSET: Final = _Unset()
DEFAULT_TIMEOUT: Final = httpx.Timeout(connect=10.0, read=60.0, write=60.0, pool=10.0)
USER_AGENT: Final = f"grepvine-python-sdk/{__version__} python-httpx/{httpx.__version__}"
THROTTLED_WAIT: Final = "grepvine_throttled_wait"
"""The response extension that records how long a client waited out 429 answers in vain."""


def coerce_timeout(timeout: float | httpx.Timeout | None) -> httpx.Timeout:
    if timeout is None:
        return DEFAULT_TIMEOUT
    if isinstance(timeout, httpx.Timeout):
        return timeout
    return httpx.Timeout(float(timeout))


@dataclass(frozen=True, slots=True, kw_only=True)
class ClientConfig:
    """The settings a client resolved for its requests."""

    endpoint: str
    api_key: str | None
    timeout: httpx.Timeout
    retry: RetryPolicy
    user_agent: str
    config_path: Path


class Throttle:
    """The client-wide pause that a 429 answer imposes on every request."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._until = 0.0

    def slow(self, now: float, delay: float) -> bool:
        """Extend the pause to at least ``now + delay``; True when this starts a new pause."""
        with self._lock:
            fresh = self._until <= now
            self._until = max(self._until, now + delay)
            return fresh

    def remaining(self, now: float) -> float:
        with self._lock:
            return max(0.0, self._until - now)


class ClientState:
    """Everything a client holds apart from its HTTP connections.

    Settings resolve lazily on first use and are cached until
    :meth:`configure` changes them. Every request reads a snapshot, so
    reconfiguring never disturbs a request in flight.
    """

    def __init__(
        self,
        *,
        api_key: str | None,
        endpoint: str | None,
        timeout: float | httpx.Timeout | None,
        retry: RetryPolicy | None,
        config_path: str | os.PathLike[str] | None,
        env: Mapping[str, str] | None,
    ) -> None:
        self._lock = threading.RLock()
        self._api_key = api_key
        self._endpoint = endpoint
        self._timeout = coerce_timeout(timeout)
        self._retry = retry or RetryPolicy()
        self._config_path = None if config_path is None else Path(config_path)
        self._env = env
        self._config: ClientConfig | None = None
        self._session: Session | None = None
        self.generation = 0
        self.closed = False
        self.throttle = Throttle()
        self.rng = random.Random()
        self.new_id: Callable[[], str] = lambda: uuid.uuid4().hex

    @property
    def lock(self) -> threading.RLock:
        return self._lock

    @property
    def resolved(self) -> ClientConfig | None:
        """The settings if they were resolved already, else None."""
        with self._lock:
            return self._config

    @property
    def session(self) -> Session | None:
        with self._lock:
            return self._session

    @property
    def retry(self) -> RetryPolicy:
        with self._lock:
            return self._retry

    def set_session(self, session: Session | None) -> None:
        with self._lock:
            self._session = session
            self.generation += 1

    def rotate_csrf(self, token: str | None) -> None:
        """Adopt the CSRF token a response issued for the current session."""
        with self._lock:
            if token and self._session is not None and token != self._session.csrf_token:
                self._session = replace(self._session, csrf_token=token)
                self.generation += 1

    def config(self) -> ClientConfig:
        """The resolved settings, resolving them on first use."""
        with self._lock:
            if self._config is None:
                credentials = resolve_credentials(
                    endpoint=self._endpoint,
                    api_key=self._api_key,
                    env=os.environ if self._env is None else self._env,
                    config_path=self._config_path,
                )
                self._config = ClientConfig(
                    endpoint=credentials.endpoint,
                    api_key=credentials.api_key,
                    timeout=self._timeout,
                    retry=self._retry,
                    user_agent=USER_AGENT,
                    config_path=credentials.config_path,
                )
            return self._config

    def configure(
        self,
        *,
        api_key: str | _Unset | None = UNSET,
        endpoint: str | _Unset | None = UNSET,
        timeout: float | httpx.Timeout | _Unset | None = UNSET,
        retry: RetryPolicy | _Unset | None = UNSET,
        config_path: str | os.PathLike[str] | _Unset | None = UNSET,
    ) -> None:
        with self._lock:
            if not isinstance(api_key, _Unset):
                self._api_key = api_key
            if not isinstance(endpoint, _Unset):
                self._endpoint = endpoint
            if not isinstance(timeout, _Unset):
                self._timeout = coerce_timeout(timeout)
            if not isinstance(retry, _Unset):
                self._retry = retry or RetryPolicy()
            if not isinstance(config_path, _Unset):
                self._config_path = None if config_path is None else Path(config_path)
            self._config = None
            self.generation += 1
            self.closed = False

    def close(self) -> None:
        with self._lock:
            self.closed = True

    def check_open(self) -> None:
        if self.closed:
            raise RuntimeError("the client is closed; call configure() to use it again")

    def headers(self, config: ClientConfig) -> dict[str, str]:
        """The headers every request carries: identification and credentials.

        A signed-in session takes the place of the API key until it ends.
        """
        headers = {"User-Agent": config.user_agent}
        session = self.session
        if session is not None:
            headers["Cookie"] = f"{session.cookie_name}={session.cookie}"
            headers["X-Csrf-Token"] = session.csrf_token
        elif config.api_key is not None:
            headers["Authorization"] = f"Bearer {config.api_key}"
        return headers

    def check_credentials(self, config: ClientConfig) -> None:
        if config.api_key is None and self.session is None:
            raise ConfigurationError(NOT_LOGGED_IN_MESSAGE)


class _Retrying:
    """The retry loop shared by both transports; see :mod:`grepvine_sdk._core.retry`.

    The same request (same body, same ``Idempotency-Key``) is sent on every
    attempt. A 429 that exhausted the wait budget is returned with the time
    waited recorded in its extensions, so its error says so.
    """

    def __init__(self, state: ClientState, clock: Callable[[], Callable[[], float]]) -> None:
        self.state = state
        self.clock = clock

    def throttle_wait(self) -> float:
        return self.state.throttle.remaining(self.clock()())

    def decide(
        self, outcome: httpx.Response | httpx.TransportError, attempt: int, waited: float
    ) -> Deliver | Fail | PauseThen | BackoffThen:
        decision = decide(
            outcome,
            attempt=attempt,
            throttled_wait=waited,
            policy=self.state.retry,
            rng=self.state.rng,
        )
        if isinstance(decision, PauseThen):
            # Only extend the client-wide deadline; the next attempt waits it out, so a pause
            # another request lengthened meanwhile is honoured in full.
            self.state.throttle.slow(self.clock()(), decision.seconds)
        if isinstance(decision, Deliver) and decision.throttled_wait is not None:
            assert isinstance(outcome, httpx.Response)
            outcome.extensions[THROTTLED_WAIT] = decision.throttled_wait
        return decision


class RetryTransport(httpx.BaseTransport):
    """Retries a request on 429, 5xx and connection failures, per the client's policy."""

    def __init__(
        self,
        inner: httpx.BaseTransport,
        state: ClientState,
        sleep: Callable[[], Callable[[float], None]],
        clock: Callable[[], Callable[[], float]],
    ) -> None:
        self._inner = inner
        self._retrying = _Retrying(state, clock)
        self._sleep = sleep

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        attempt, waited = 1, 0.0
        while True:
            if (wait := self._retrying.throttle_wait()) > 0:
                self._sleep()(wait)
            outcome: httpx.Response | httpx.TransportError
            try:
                outcome = self._inner.handle_request(request)
            except httpx.TransportError as exc:
                outcome = exc
            decision = self._retrying.decide(outcome, attempt, waited)
            if isinstance(decision, Deliver):
                assert isinstance(outcome, httpx.Response)
                return outcome
            if isinstance(outcome, httpx.TransportError):
                if isinstance(decision, Fail):
                    raise outcome
            else:
                outcome.close()
            if isinstance(decision, PauseThen):
                waited += decision.seconds
            elif isinstance(decision, BackoffThen):
                attempt += 1
                self._sleep()(decision.seconds)

    def close(self) -> None:
        self._inner.close()


class AsyncRetryTransport(httpx.AsyncBaseTransport):
    """The asynchronous twin of :class:`RetryTransport`."""

    def __init__(
        self,
        inner: httpx.AsyncBaseTransport,
        state: ClientState,
        sleep: Callable[[], Callable[[float], Awaitable[None]]],
        clock: Callable[[], Callable[[], float]],
    ) -> None:
        self._inner = inner
        self._retrying = _Retrying(state, clock)
        self._sleep = sleep

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        attempt, waited = 1, 0.0
        while True:
            if (wait := self._retrying.throttle_wait()) > 0:
                await self._sleep()(wait)
            outcome: httpx.Response | httpx.TransportError
            try:
                outcome = await self._inner.handle_async_request(request)
            except httpx.TransportError as exc:
                outcome = exc
            decision = self._retrying.decide(outcome, attempt, waited)
            if isinstance(decision, Deliver):
                assert isinstance(outcome, httpx.Response)
                return outcome
            if isinstance(outcome, httpx.TransportError):
                if isinstance(decision, Fail):
                    raise outcome
            else:
                await outcome.aclose()
            if isinstance(decision, PauseThen):
                waited += decision.seconds
            elif isinstance(decision, BackoffThen):
                attempt += 1
                await self._sleep()(decision.seconds)

    async def aclose(self) -> None:
        await self._inner.aclose()


def raise_for_error(response: httpx.Response) -> None:
    """Raise the :class:`~grepvine_sdk.APIError` an error response stands for."""
    if response.status_code < 400:
        return
    waited = response.extensions.get(THROTTLED_WAIT)
    suffix = "" if waited is None else f" (slowed down for {int(waited)}s without success)"
    raise map_error(response, message_suffix=suffix)


def check_response(response: httpx.Response) -> None:
    """A response hook that raises before an error body reaches an operation's decoder."""
    if response.status_code >= 400:
        response.read()
        raise_for_error(response)


async def acheck_response(response: httpx.Response) -> None:
    if response.status_code >= 400:
        await response.aread()
        raise_for_error(response)


def http_client_options(state: ClientState, config: ClientConfig) -> dict[str, Any]:
    """The settings of an HTTPX client for the current configuration and session."""
    return {
        "base_url": config.endpoint,
        "headers": state.headers(config),
        "timeout": config.timeout,
    }
