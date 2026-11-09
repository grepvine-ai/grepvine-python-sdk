"""The synchronous and asynchronous clients."""

from __future__ import annotations

import os
from importlib.metadata import version
from typing import Any, Final, Self

import httpx

from grepvine._config import Settings, resolve
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
from grepvine._index import AsyncIndexClient, IndexClient
from grepvine._retry import AsyncRetryTransport, RetryPolicy, RetryTransport
from grepvine.errors import ConfigurationError, map_error

DEFAULT_TIMEOUT: Final = 60.0
__all__ = ["AsyncClient", "Client", "default_client", "index", "set_default_client"]


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


def _qualify(settings: Settings, name: str) -> str:
    if "/" in name:
        return name
    if not settings.organization:
        raise ConfigurationError(
            f"name the index as 'organization/{name}', or set a default organization"
        )
    return f"{settings.organization}/{name}"


def _session(http: httpx.Client | httpx.AsyncClient, response: httpx.Response) -> None:
    """Send the CSRF token a sign-in issued with every later request; httpx keeps the cookie."""
    if token := response.headers.get("x-csrf-token"):
        http.headers["X-Csrf-Token"] = token


class Client(_GeneratedClient):
    """A client of the Grepvine API.

    ``Client()`` with no arguments is configured like ``gv``; see below.

    Each of ``api_key``, ``endpoint`` and ``organization`` is taken from its
    argument, else from its environment variable (``GREPVINE_API_KEY``,
    ``GREPVINE_API_ENDPOINT``, ``GREPVINE_ORGANIZATION``), else from the
    configuration file that ``gv`` writes, else from its default. Clients
    configured differently can be used side by side.

    Args:
        api_key: The API key sent as a bearer token. Without one, only the
            methods that need no credentials work, such as ``account.login``
            and ``device_login.authorize``; after ``account.login`` the
            client uses the signed-in session.
        endpoint: The service URL, with or without ``/v1``. Default:
            ``https://api.grepvine.ai``.
        organization: The organization of an index named without one, as in
            ``client.index("support")``.
        config_file: The configuration file. Default: ``$GREPVINE_CONFIG``,
            else ``~/.grepvine/config.yaml`` when it exists. A file other
            users can read is refused.
        use_environment: Whether to read the environment variables and the
            default configuration file. With ``False``, the client uses only
            its arguments and an explicit ``config_file``.
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
        endpoint: str | None = None,
        organization: str | None = None,
        config_file: str | os.PathLike[str] | None = None,
        use_environment: bool = True,
        timeout: float | httpx.Timeout | None = DEFAULT_TIMEOUT,
        retry: RetryPolicy | None = None,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.settings = resolve(
            endpoint=endpoint,
            api_key=api_key,
            organization=organization,
            config_file=config_file,
            use_environment=use_environment,
        )
        options = _options(self.settings.api_key, self.settings.endpoint, timeout)
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
        self._connection = connection

    def index(self, name: str) -> IndexClient:
        """The index ``organization/index``, or ``index`` in the default organization.

        Making it sends no request.
        """
        return IndexClient(self._connection, _qualify(self.settings, name), self.documents)

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
        endpoint: str | None = None,
        organization: str | None = None,
        config_file: str | os.PathLike[str] | None = None,
        use_environment: bool = True,
        timeout: float | httpx.Timeout | None = DEFAULT_TIMEOUT,
        retry: RetryPolicy | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.settings = resolve(
            endpoint=endpoint,
            api_key=api_key,
            organization=organization,
            config_file=config_file,
            use_environment=use_environment,
        )
        options = _options(self.settings.api_key, self.settings.endpoint, timeout)
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
        self._connection = connection

    def index(self, name: str) -> AsyncIndexClient:
        """The index ``organization/index``, or ``index`` in the default organization.

        Making it sends no request.
        """
        return AsyncIndexClient(self._connection, _qualify(self.settings, name), self.documents)

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


_default: Client | None = None


def default_client() -> Client:
    """The client that `index` uses: ``Client()``, created on first use."""
    global _default
    if _default is None:
        _default = Client()
    return _default


def set_default_client(client: Client | None) -> None:
    """Make ``client`` the one `index` uses; ``None`` creates a new one on next use."""
    global _default
    _default = client


def index(name: str) -> IndexClient:
    """The index ``name`` of the default client; see `Client.index`."""
    return default_client().index(name)
