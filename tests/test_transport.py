import asyncio
import json
from collections.abc import Iterator
from email import policy
from email.parser import BytesParser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO
from threading import Thread
from typing import Any
from urllib.parse import parse_qs, urlsplit

import httpx
import pytest

from grepvine_sdk import UNSET, AuthenticatedClient, Client, File
from grepvine_sdk.generated.api.device_login import poll_device_token, start_device_authorization
from grepvine_sdk.generated.api.indexes import update_index
from grepvine_sdk.generated.api.objects import get_document, put_document, put_objects
from grepvine_sdk.generated.api.search import query_index
from grepvine_sdk.generated.models import (
    APIKeyCreated,
    DeviceAuthorization,
    DeviceAuthorizationRequest,
    DeviceTokenRequest,
    Error,
    Metadata,
    MutationBatchResult,
    MutationResult,
    PutDocumentForm,
    PutDocumentIfNoneMatch,
    QueryPage,
    QueryRequest,
    UpdateIndexRequest,
)

PAGINATION = {"next_page_id": "", "has_next": False}


@pytest.fixture
def server() -> Iterator[tuple[str, list[dict[str, Any]], dict[str, Any]]]:
    requests: list[dict[str, Any]] = []
    reply: dict[str, Any] = {
        "status": 200,
        "body": {"results": [], "pagination": PAGINATION},
        "headers": {"Content-Type": "application/json", "X-Request-ID": "req-123"},
    }

    class Handler(BaseHTTPRequestHandler):
        def handle_request(self) -> None:
            body = self.rfile.read(int(self.headers.get("Content-Length", "0")))
            requests.append(
                {"path": self.path, "method": self.command, "headers": self.headers, "body": body}
            )
            payload = reply["body"]
            data = payload if isinstance(payload, bytes) else json.dumps(payload).encode()
            self.send_response(reply["status"])
            for name, value in reply["headers"].items():
                self.send_header(name, value)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        do_GET = handle_request
        do_POST = handle_request
        do_PUT = handle_request
        do_PATCH = handle_request

        def log_message(self, format: str, *args: Any) -> None:
            pass

    httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{httpd.server_port}/v1", requests, reply
    finally:
        httpd.shutdown()
        httpd.server_close()
        thread.join()


def test_sync_async_search_and_independent_credentials(server: Any) -> None:
    base_url, requests, _ = server
    with AuthenticatedClient(base_url=base_url, token="gvk_one") as client:
        result = query_index.sync_detailed(
            "acme",
            "notes",
            client=client,
            body=QueryRequest(pattern="hello"),
            page="next /+?",
            amount=2,
        )
        assert isinstance(result.parsed, QueryPage)
        assert not result.parsed.pagination.has_next

    async def search() -> None:
        async with AuthenticatedClient(base_url=base_url, token="gvk_two") as client:
            result = await query_index.asyncio_detailed(
                "acme", "notes", client=client, body=QueryRequest(pattern="hello")
            )
            assert isinstance(result.parsed, QueryPage)

    asyncio.run(search())
    assert [r["headers"]["Authorization"] for r in requests] == ["Bearer gvk_one", "Bearer gvk_two"]
    assert requests[0]["headers"]["Cookie"] is None
    url = urlsplit(requests[0]["path"])
    assert url.path == "/v1/organizations/acme/indexes/notes/query"
    assert parse_qs(url.query)["page"] == ["next /+?"]
    assert json.loads(requests[0]["body"])["pattern"] == "hello"


def test_multipart_binary_metadata_and_preconditions(server: Any) -> None:
    base_url, requests, reply = server
    reply["body"] = {"key": "café/a.bin", "revision": "rev"}
    metadata = '{"count":{"type":"integer","value":123}}'
    content = bytes([0, 255, 128, 10])
    with AuthenticatedClient(base_url=base_url, token="gvk_test") as client:
        result = put_document.sync_detailed(
            "acme",
            "notes",
            client=client,
            body=PutDocumentForm(
                key="café/a.bin", content=File(BytesIO(content), "a.bin"), metadata=metadata
            ),
            idempotency_key="stable-operation-123",
            if_none_match=PutDocumentIfNoneMatch.VALUE_0,
        )
    assert isinstance(result.parsed, MutationResult)
    assert result.parsed.revision == "rev"
    request = requests[0]
    message = BytesParser(policy=policy.default).parsebytes(
        b"Content-Type: "
        + request["headers"]["Content-Type"].encode()
        + b"\r\n\r\n"
        + request["body"]
    )
    parts = {
        part.get_param("name", header="content-disposition"): part.get_payload(decode=True)
        for part in message.iter_parts()
    }
    assert parts == {
        "key": "café/a.bin".encode(),
        "metadata": metadata.encode(),
        "content": content,
    }
    assert request["headers"]["Idempotency-Key"] == "stable-operation-123"
    assert request["headers"]["If-None-Match"] == "*"


def test_raw_ndjson_and_per_document_failures(server: Any) -> None:
    base_url, requests, reply = server
    reply["body"] = {
        "results": [
            {"key": "a", "revision": "r1"},
            {
                "key": "b",
                "error": {
                    "code": "precondition_failed",
                    "reason": "revision",
                    "error": "Check the revision.",
                },
            },
        ]
    }
    body = b'{"key":"a","content":"hello\\nworld"}\n{"key":"b","content":"bye"}\n'
    with AuthenticatedClient(base_url=base_url, token="gvk_test") as client:
        result = put_objects.sync_detailed(
            "acme",
            "notes",
            client=client,
            body=File(BytesIO(body)),
            idempotency_key="stable-operation-123",
        )
    assert requests[0]["body"] == body
    assert requests[0]["headers"]["Content-Type"] == "application/x-ndjson"
    assert isinstance(result.parsed, MutationBatchResult)
    assert isinstance(result.parsed.results[1].error, Error)
    assert result.parsed.results[1].error.code == "precondition_failed"


@pytest.mark.parametrize("status", [200, 206])
def test_binary_download_path_encoding_and_headers(server: Any, status: int) -> None:
    base_url, requests, reply = server
    reply.update(
        status=status,
        body=bytes([0, 255, 128, 10]),
        headers={
            "Content-Type": "application/octet-stream",
            "ETag": "rev",
            "Content-Range": "bytes 0-3/10",
            "X-Grepvine-Metadata": "{}",
        },
    )
    with AuthenticatedClient(base_url=base_url, token="gvk_test") as client:
        result = get_document.sync_detailed(
            "acme", "notes", "dir/café %?.bin", client=client, range_="bytes=0-3"
        )
    assert result.status_code == status
    assert result.content == bytes([0, 255, 128, 10])
    assert isinstance(result.parsed, File)
    assert result.parsed.payload.read() == result.content
    assert result.headers["ETag"] == "rev"
    assert result.headers["X-Grepvine-Metadata"] == "{}"
    assert requests[0]["path"] == (
        "/v1/organizations/acme/indexes/notes/objects/dir%2Fcaf%C3%A9%20%25%3F.bin"
    )
    assert requests[0]["headers"]["Range"] == "bytes=0-3"


@pytest.mark.parametrize("status", [429, 416])
def test_errors_preserve_status_request_id_and_retry_after(server: Any, status: int) -> None:
    base_url, requests, reply = server
    reply.update(
        status=status, body={"code": "busy", "reason": "capacity", "error": "Slow down and retry."}
    )
    reply["headers"]["Retry-After"] = "2"
    with AuthenticatedClient(base_url=base_url, token="gvk_test") as client:
        result = get_document.sync_detailed("acme", "notes", "a", client=client)
    assert isinstance(result.parsed, Error)
    assert result.status_code == status
    assert result.parsed.code == "busy"
    assert result.headers["X-Request-ID"] == "req-123"
    assert result.headers["Retry-After"] == "2"
    assert len(requests) == 1


def test_cookie_csrf_and_null_vs_absent_tags(server: Any) -> None:
    base_url, requests, reply = server
    reply.update(status=400, body={"code": "bad_request", "reason": "test", "error": "test"})
    with Client(base_url=base_url, cookies={"__Host-grepvine-session": "session"}) as client:
        body = UpdateIndexRequest.from_dict({"tags": {"old": None, "kept": "new"}})
        update_index.sync_detailed(
            "acme", "notes", client=client, body=body, x_csrf_token="csrf-token"
        )
    assert json.loads(requests[0]["body"]) == {"tags": {"old": None, "kept": "new"}}
    assert requests[0]["headers"]["Cookie"] == "__Host-grepvine-session=session"
    assert requests[0]["headers"]["X-Csrf-Token"] == "csrf-token"
    assert requests[0]["headers"]["Authorization"] is None
    assert UpdateIndexRequest().tags is UNSET


def test_all_metadata_variants_and_large_integers() -> None:
    data = {
        "s": {"type": "string", "value": "hello"},
        "i": {"type": "integer", "value": 9223372036854775807},
        "n": {"type": "number", "value": 1.25},
        "b": {"type": "boolean", "value": True},
        "t": {"type": "timestamp", "value": "2026-10-13T12:00:00+00:00"},
    }
    assert Metadata.from_dict(data).to_dict() == data


def test_async_timeout_closes_transport() -> None:
    async def slow(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("Timed out", request=request)

    async def call() -> None:
        transport = httpx.MockTransport(slow)
        async with AuthenticatedClient(
            base_url="https://example.test/v1",
            token="gvk",
            timeout=httpx.Timeout(0.1),
            httpx_args={"transport": transport},
        ) as client:
            with pytest.raises(httpx.ReadTimeout):
                await query_index.asyncio(
                    "acme", "notes", client=client, body=QueryRequest(pattern="hello")
                )
            connection = client.get_async_httpx_client()
        assert connection.is_closed

    asyncio.run(call())


def test_anonymous_device_flow_returns_an_api_key_usable_for_search(server: Any) -> None:
    base_url, requests, reply = server
    reply["body"] = {
        "device_code": "device-code",
        "user_code": "ABCD-EFGH",
        "verification_uri": "https://example.test/device",
        "verification_uri_complete": "https://example.test/device?code=ABCD-EFGH",
        "expires_in": 600,
        "interval": 5,
    }
    with Client(base_url=base_url) as anonymous:
        started = start_device_authorization.sync(
            client=anonymous, body=DeviceAuthorizationRequest(api_key_name="sdk-test")
        )
        assert isinstance(started, DeviceAuthorization)
        reply.update(
            status=400,
            body={
                "code": "authorization_pending",
                "reason": "authorization",
                "error": "Complete authorization in your browser.",
            },
        )
        pending = poll_device_token.sync_detailed(
            client=anonymous, body=DeviceTokenRequest(device_code=started.device_code)
        )
        assert pending.status_code == 400 and isinstance(pending.parsed, Error)
        assert pending.parsed.code == "authorization_pending"
        reply.update(
            status=200,
            body={
                "id": "00000000-0000-4000-8000-000000000001",
                "name": "sdk-test",
                "prefix": "gvk_",
                "key": "gvk_from_device",
                "created_at": "2026-10-13T12:00:00Z",
            },
        )
        token = poll_device_token.sync(
            client=anonymous, body=DeviceTokenRequest(device_code=started.device_code)
        )
        assert isinstance(token, APIKeyCreated)
    assert all(request["headers"]["Authorization"] is None for request in requests)
    assert json.loads(requests[0]["body"]) == {"api_key_name": "sdk-test"}
    assert json.loads(requests[1]["body"]) == {"device_code": "device-code"}
    reply["body"] = {"results": [], "pagination": PAGINATION}
    with AuthenticatedClient(base_url=base_url, token=token.key) as client:
        result = query_index.sync(
            "acme", "notes", client=client, body=QueryRequest(pattern="hello")
        )
        assert isinstance(result, QueryPage)
    assert requests[-1]["headers"]["Authorization"] == "Bearer gvk_from_device"
