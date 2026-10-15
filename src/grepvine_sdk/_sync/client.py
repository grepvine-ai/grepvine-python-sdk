"""The synchronous client."""

from __future__ import annotations

import os
import time
from collections.abc import Callable, Mapping
from typing import Any, TypeVar, cast

import httpx

from grepvine_sdk._core.effects import Call, Notify, Now, Op, SetSession, Sleep
from grepvine_sdk._core.retry import RetryPolicy
from grepvine_sdk._generated.client import Client as _OperationClient
from grepvine_sdk._http import (
    UNSET,
    ClientConfig,
    ClientState,
    RetryTransport,
    _Unset,
    check_response,
    http_client_options,
)
from grepvine_sdk._sync.resources import (
    Account,
    APIKeys,
    DeviceLogin,
    Indexes,
    Organizations,
)
from grepvine_sdk.errors import GrepvineError, TransportError

T = TypeVar("T")


class Client:
    """A synchronous Grepvine client.

    Without arguments the endpoint and API key come from the same places the
    ``gv`` command-line client uses: the ``GREPVINE_API_ENDPOINT`` (or
    ``GREPVINE_ENDPOINT``) and ``GREPVINE_API_KEY`` environment variables, then
    ``~/.grepvine/config.yaml`` as written by ``gv login``. Explicit arguments
    win. Nothing is resolved until the first request.

    ``timeout`` is in seconds or an ``httpx.Timeout``; ``retry`` changes how
    failed requests are retried. ``env`` replaces the environment the settings
    are read from, and ``transport`` the HTTPX transport requests travel
    through, for example ``httpx.MockTransport`` in tests.

    The client is safe to share between threads.
    """

    def __init__(
        self,
        *,
        api_key: str | None = None,
        endpoint: str | None = None,
        timeout: float | httpx.Timeout | None = None,
        retry: RetryPolicy | None = None,
        config_path: str | os.PathLike[str] | None = None,
        env: Mapping[str, str] | None = None,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._state = ClientState(
            api_key=api_key,
            endpoint=endpoint,
            timeout=timeout,
            retry=retry,
            config_path=config_path,
            env=env,
        )
        self._transport_option = transport
        self._transport: RetryTransport | None = None
        self._clients: tuple[int, httpx.Client, _OperationClient] | None = None
        self._sleep: Callable[[float], None] = time.sleep
        self._clock: Callable[[], float] = time.monotonic
        self.organizations = Organizations(self)
        """The organizations the caller belongs to, and their members."""
        self.indexes = Indexes(self)
        """The indexes of every organization, referenced as ``"organization/index"``."""
        self.api_keys = APIKeys(self)
        """The API keys of the signed-in user."""
        self.account = Account(self)
        """Registration, sign-in and the signed-in user's account."""
        self.device_login = DeviceLogin(self)
        """Issuing an API key to a device once a signed-in user approves it."""

    @property
    def config(self) -> ClientConfig:
        """The resolved settings; resolving them reads the environment and configuration file."""
        return self._state.config()

    @property
    def http(self) -> httpx.Client:
        """An ``httpx.Client`` for requests the resources do not cover.

        It sends requests relative to the configured endpoint (``/v1``
        included) with the client's credentials, timeout and retries, and
        returns every response as it is, errors included::

            response = client.http.get("/organizations", params={"amount": 10})
            response.raise_for_status()

        It changes when the client is reconfigured or signs in or out, so read
        it again rather than keeping it.
        """
        return self._http_clients()[0]

    def configure(
        self,
        *,
        api_key: str | _Unset | None = UNSET,
        endpoint: str | _Unset | None = UNSET,
        timeout: float | httpx.Timeout | _Unset | None = UNSET,
        retry: RetryPolicy | _Unset | None = UNSET,
        config_path: str | os.PathLike[str] | _Unset | None = UNSET,
    ) -> None:
        """Change settings in place. Passing ``None`` returns a setting to the default chain."""
        self._state.configure(
            api_key=api_key,
            endpoint=endpoint,
            timeout=timeout,
            retry=retry,
            config_path=config_path,
        )

    def close(self) -> None:
        """Close the connection pool. :meth:`configure` reopens the client."""
        with self._state.lock:
            self._state.close()
            transport, self._transport = self._transport, None
            self._clients = None
        if transport is not None:
            transport.close()

    def __enter__(self) -> Client:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    def __repr__(self) -> str:
        resolved = self._state.resolved
        if resolved is None:
            return "<grepvine_sdk.Client unresolved>"
        return f"<grepvine_sdk.Client endpoint={resolved.endpoint!r}>"

    def _http_clients(self) -> tuple[httpx.Client, _OperationClient]:
        """The HTTPX client for :attr:`http` and the one operations use, built for the settings."""
        state = self._state
        with state.lock:
            state.check_open()
            config = state.config()
            if self._clients is None or self._clients[0] != state.generation:
                if self._transport is None:
                    self._transport = RetryTransport(
                        self._transport_option or httpx.HTTPTransport(),
                        state,
                        lambda: self._sleep,
                        lambda: self._clock,
                    )
                options = http_client_options(state, config)
                public = httpx.Client(transport=self._transport, **options)
                internal = httpx.Client(
                    transport=self._transport,
                    event_hooks={"response": [check_response]},
                    **options,
                )
                operations = _OperationClient(base_url=config.endpoint).set_httpx_client(internal)
                self._clients = (state.generation, public, operations)
            return self._clients[1], self._clients[2]

    def _operations(self, *, auth: bool) -> _OperationClient:
        operations = self._http_clients()[1]
        if auth:
            self._state.check_credentials(self._state.config())
        return operations

    def _perform(self, effect: Any) -> Any:
        if isinstance(effect, Call):
            operations = self._operations(auth=effect.auth)
            try:
                response = effect.operation.sync_detailed(
                    *effect.args, client=operations, **effect.kwargs
                )
            except httpx.TransportError as exc:
                raise TransportError(str(exc) or type(exc).__name__, cause=exc) from exc
            except (KeyError, ValueError, TypeError) as exc:
                raise GrepvineError("the service returned a response the SDK cannot read") from exc
            self._state.rotate_csrf(response.headers.get("x-csrf-token"))
            return response
        if isinstance(effect, Sleep):
            self._sleep(effect.seconds)
            return None
        if isinstance(effect, Now):
            return self._clock()
        if isinstance(effect, Notify):
            effect.callback(effect.value)
            return None
        if isinstance(effect, SetSession):
            self._state.set_session(effect.session)
            return None
        raise TypeError(f"unknown effect {effect!r}")  # pragma: no cover

    def _run(self, op: Op[T]) -> T:
        """Drive an operation to completion, performing its effects."""
        try:
            effect = next(op)
            while True:
                try:
                    result = self._perform(effect)
                except GrepvineError as exc:
                    effect = op.throw(exc)
                else:
                    effect = op.send(result)
        except StopIteration as stop:
            return cast(T, stop.value)
        finally:
            op.close()
