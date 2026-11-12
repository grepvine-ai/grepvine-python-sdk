"""Requests go through the proxy that HTTP(S)_PROXY names, except to NO_PROXY hosts, whatever
trust_env says; a transport given in code is used instead, and still retried."""

from __future__ import annotations

import json
import threading
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

import httpx
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
    "permissions": ["search", "read"],
    "created_at": "2026-01-01T00:00:00Z",
}


class Recorder(ThreadingHTTPServer):
    """A local HTTP server that answers every GET with an index, recording each request line.

    A proxy is sent the absolute URL (``GET http://host/v1/...``); an origin server, the path.
    """

    def __init__(self) -> None:
        self.paths: list[str] = []
        self.failures = 0
        recorder = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:
                recorder.paths.append(self.path)
                status, answer = 200, INDEX
                if recorder.failures:
                    recorder.failures -= 1
                    status, answer = 503, {"code": "unavailable", "reason": "r", "error": "busy"}
                body = json.dumps(answer).encode()
                self.send_response(status)
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


def test_trust_env_false_still_uses_the_proxy_variable(
    proxy: Recorder, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("HTTP_PROXY", proxy.url)
    get_index(grepvine.Client(api_key="k", endpoint="http://grepvine.test", trust_env=False))
    assert proxy.paths == [f"http://grepvine.test{PATH}"]


def test_a_transport_with_a_proxy_is_used_and_retried(proxy: Recorder) -> None:
    proxy.failures = 1
    transport = httpx.HTTPTransport(proxy=proxy.url)
    client = grepvine.Client(
        api_key="k",
        endpoint="http://grepvine.test",
        transport=transport,
        retry=grepvine.RetryPolicy(backoff=(0.0,)),
    )
    get_index(client)
    assert proxy.paths == [f"http://grepvine.test{PATH}"] * 2


def test_a_transport_is_used_instead_of_the_proxy_variable(
    proxy: Recorder, origin: Recorder, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("HTTP_PROXY", proxy.url)
    get_index(grepvine.Client(api_key="k", endpoint=origin.url, transport=httpx.HTTPTransport()))
    assert (proxy.paths, origin.paths) == ([], [PATH])


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
