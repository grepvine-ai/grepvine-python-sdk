"""Requests go through the proxy that HTTP(S)_PROXY or proxy= names, unless NO_PROXY or
trust_env=False says otherwise."""

from __future__ import annotations

import json
import threading
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

import pytest

import grepvine

pytestmark = pytest.mark.anyio

INDEX = {
    "id": "00000000-0000-0000-0000-000000000001",
    "organization": "acme",
    "name": "docs",
    "canonical_id": "c",
    "description": "",
    "tags": {},
    "state": "ready",
    "document_count": 0,
    "content_bytes": 0,
    "created_at": "2026-01-01T00:00:00Z",
}


class Recorder(ThreadingHTTPServer):
    """A local HTTP server that answers every GET with an index, recording each request line.

    A proxy is sent the absolute URL (``GET http://host/v1/...``); an origin server, the path.
    """

    def __init__(self) -> None:
        self.paths: list[str] = []
        recorder = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:
                recorder.paths.append(self.path)
                body = json.dumps(INDEX).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *_: Any) -> None:
                pass

        super().__init__(("127.0.0.1", 0), Handler)

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self.server_address[1]}"


@pytest.fixture
def proxy() -> Iterator[Recorder]:
    server = Recorder()
    threading.Thread(target=server.serve_forever, args=(0.01,), daemon=True).start()
    yield server
    server.shutdown()
    server.server_close()


@pytest.fixture
def origin() -> Iterator[Recorder]:
    server = Recorder()
    threading.Thread(target=server.serve_forever, args=(0.01,), daemon=True).start()
    yield server
    server.shutdown()
    server.server_close()


PATH = "/v1/organizations/acme/indexes/docs"


def get_index(client: Any) -> None:
    with client:
        client.indexes.get("acme", "docs")


async def aget_index(client: Any) -> None:
    async with client:
        await client.indexes.get("acme", "docs")


def test_http_proxy_variable_is_used(proxy: Recorder, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HTTP_PROXY", proxy.url)
    get_index(grepvine.Client(api_key="k", endpoint="http://grepvine.test"))
    assert proxy.paths == [f"http://grepvine.test{PATH}"]


async def test_async_client_uses_the_proxy_variable(
    proxy: Recorder, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("HTTP_PROXY", proxy.url)
    await aget_index(grepvine.AsyncClient(api_key="k", endpoint="http://grepvine.test"))
    assert proxy.paths == [f"http://grepvine.test{PATH}"]


def test_no_proxy_connects_directly(
    proxy: Recorder, origin: Recorder, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("HTTP_PROXY", proxy.url)
    monkeypatch.setenv("NO_PROXY", "127.0.0.1")
    get_index(grepvine.Client(api_key="k", endpoint=origin.url))
    assert (proxy.paths, origin.paths) == ([], [PATH])


def test_trust_env_false_ignores_the_proxy_variable(
    proxy: Recorder, origin: Recorder, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("HTTP_PROXY", proxy.url)
    get_index(grepvine.Client(api_key="k", endpoint=origin.url, trust_env=False))
    assert (proxy.paths, origin.paths) == ([], [PATH])


def test_proxy_argument_is_used_without_variables(proxy: Recorder) -> None:
    get_index(
        grepvine.Client(
            api_key="k", endpoint="http://grepvine.test", proxy=proxy.url, trust_env=False
        )
    )
    assert proxy.paths == [f"http://grepvine.test{PATH}"]


@pytest.mark.parametrize("make", ["from_env", "from_config"])
def test_from_env_and_from_config_use_the_proxy_variable(
    make: str, proxy: Recorder, monkeypatch: pytest.MonkeyPatch, tmp_path: Any
) -> None:
    monkeypatch.setenv("HTTP_PROXY", proxy.url)
    monkeypatch.setenv("GREPVINE_API_ENDPOINT", "http://grepvine.test")
    path = tmp_path / "c.yaml"
    path.write_text("endpoint: http://grepvine.test\n")
    path.chmod(0o600)
    client = grepvine.Client.from_env() if make == "from_env" else grepvine.Client.from_config(path)
    get_index(client)
    assert proxy.paths == [f"http://grepvine.test{PATH}"]


def test_proxy_and_transport_are_exclusive() -> None:
    import httpx

    with pytest.raises(grepvine.ConfigurationError, match="proxy or a transport"):
        grepvine.Client(proxy="http://proxy.test:3128", transport=httpx.MockTransport(lambda r: r))
