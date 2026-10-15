"""The synchronous and asynchronous clients."""

from __future__ import annotations

from importlib.metadata import version
from typing import Any, Final, Self

import httpx

from grepvine._generated.api.resources import _GeneratedAsyncClient, _GeneratedClient
from grepvine._generated.client import Client as _Connection
from grepvine._helpers import (
    AsyncDeviceLogin,
    AsyncDocuments,
    AsyncIndexes,
    DeviceLogin,
    Documents,
    Indexes,
)
from grepvine._retry import AsyncRetryTransport, RetryPolicy, RetryTransport
from grepvine.errors import ConfigurationError, map_error

DEFAULT_ENDPOINT: Final = "https://api.grepvine.ai"
DEFAULT_TIMEOUT: Final = 60.0
__all__ = ["AsyncClient", "Client"]


def _options(
    api_key: str | None, endpoint: str, timeout: float | httpx.Timeout | None
) -> dict[str, Any]:
    url = endpoint.rstrip("/")
    if not url.startswith(("https://", "http://")):
        raise ConfigurationError(f"the endpoint must be an http or https URL, not {endpoint!r}")
    headers = {"User-Agent": f"grepvine-python/{version('grepvine')} httpx/{httpx.__version__}"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    return {
        "base_url": url if url.endswith("/v1") else f"{url}/v1",
        "headers": headers,
        "timeout": timeout,
    }


def _session(http: httpx.Client | httpx.AsyncClient, response: httpx.Response) -> None:
    """Send the CSRF token a sign-in issued with every later request; httpx keeps the cookie."""
    if token := response.headers.get("x-csrf-token"):
        http.headers["X-Csrf-Token"] = token


class Client(_GeneratedClient):
    """A client of the Grepvine API.

    Args:
        api_key: The API key sent as a bearer token. Without one, only the
            methods that need no credentials work, such as ``account.login``
            and ``device_login.authorize``; after ``account.login`` the
            client uses the signed-in session.
        endpoint: The service URL, with or without ``/v1``.
        timeout: Seconds, or an ``httpx.Timeout``, for each request.
        retry: How requests are retried; see `RetryPolicy`.
        transport: The ``httpx`` transport requests go through, for example
            an ``httpx.MockTransport`` in tests.

    Use it as a context manager, or call `close`, to release its connections.
    `http` is the ``httpx.Client`` it sends requests with.
    """

    indexes: Indexes
    documents: Documents
    device_login: DeviceLogin

    def __init__(
        self,
        *,
        api_key: str | None = None,
        endpoint: str = DEFAULT_ENDPOINT,
        timeout: float | httpx.Timeout | None = DEFAULT_TIMEOUT,
        retry: RetryPolicy | None = None,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        options = _options(api_key, endpoint, timeout)
        inner = transport or httpx.HTTPTransport()
        self.http = httpx.Client(
            **options,
            transport=RetryTransport(inner, retry or RetryPolicy()),
            event_hooks={"response": [self._on_response]},
        )
        connection = _Connection(base_url=options["base_url"]).set_httpx_client(self.http)
        super().__init__(connection)
        self.indexes = Indexes(connection)
        self.documents = Documents(connection)
        self.device_login = DeviceLogin(connection)

    def _on_response(self, response: httpx.Response) -> None:
        _session(self.http, response)
        if response.status_code >= 400:
            response.read()
            raise map_error(response)

    def close(self) -> None:
        """Close the client's connections."""
        self.http.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


class AsyncClient(_GeneratedAsyncClient):
    """An asynchronous client of the Grepvine API.

    It takes the same arguments as `Client`, with an
    ``httpx.AsyncBaseTransport`` as ``transport``, and its methods are
    coroutines. Use it with ``async with``, or call `aclose`.
    """

    indexes: AsyncIndexes
    documents: AsyncDocuments
    device_login: AsyncDeviceLogin

    def __init__(
        self,
        *,
        api_key: str | None = None,
        endpoint: str = DEFAULT_ENDPOINT,
        timeout: float | httpx.Timeout | None = DEFAULT_TIMEOUT,
        retry: RetryPolicy | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        options = _options(api_key, endpoint, timeout)
        inner = transport or httpx.AsyncHTTPTransport()
        self.http = httpx.AsyncClient(
            **options,
            transport=AsyncRetryTransport(inner, retry or RetryPolicy()),
            event_hooks={"response": [self._on_response]},
        )
        connection = _Connection(base_url=options["base_url"]).set_async_httpx_client(self.http)
        super().__init__(connection)
        self.indexes = AsyncIndexes(connection)
        self.documents = AsyncDocuments(connection)
        self.device_login = AsyncDeviceLogin(connection)

    async def _on_response(self, response: httpx.Response) -> None:
        _session(self.http, response)
        if response.status_code >= 400:
            await response.aread()
            raise map_error(response)

    async def aclose(self) -> None:
        """Close the client's connections."""
        await self.http.aclose()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.aclose()
