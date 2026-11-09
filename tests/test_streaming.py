"""put streams content from a path, a file, or chunks; put_many reads documents lazily."""

from __future__ import annotations

import json
import os
from collections.abc import AsyncIterator, Iterator
from pathlib import Path

import httpx
import pytest

import grepvine
from tests.conftest import Flavor, Service, error

pytestmark = pytest.mark.anyio

MUTATION = {"key": "k", "revision": "r1"}


def ok(request: httpx.Request) -> httpx.Response:
    return httpx.Response(200, json=MUTATION)


def content_of(request: httpx.Request) -> bytes:
    """The bytes of the form's content part."""
    part = request.content.split(b'name="content"')[1]
    return part.split(b"\r\n\r\n", 1)[1].rsplit(b"\r\n--", 1)[0]


def metadata_of(request: httpx.Request) -> object:
    part = request.content.split(b'name="metadata"')[1]
    return json.loads(part.split(b"\r\n\r\n", 1)[1].split(b"\r\n--", 1)[0])


def chunks(count: int, size: int = 1000) -> Iterator[bytes]:
    for n in range(count):
        yield bytes([65 + n % 26]) * size


async def async_chunks(count: int, size: int = 1000) -> AsyncIterator[bytes]:
    for chunk in chunks(count, size):
        yield chunk


async def test_a_path_is_read_from_disk(fx: Flavor, service: Service, tmp_path: Path) -> None:
    service.route = ok
    path = tmp_path / "report.csv"
    path.write_bytes(b"a,b\n1,2\n")
    await fx.run(fx.client.index("acme/docs").put("exports/report.csv", path))
    request = service.requests[0]
    assert content_of(request) == b"a,b\n1,2\n"
    assert b'filename="report.csv"' in request.content
    assert "Content-Length" in request.headers


async def test_a_str_is_content_never_a_path(fx: Flavor, service: Service, tmp_path: Path) -> None:
    service.route = ok
    path = tmp_path / "report.csv"
    path.write_bytes(b"from disk")
    await fx.run(fx.client.index("acme/docs").put("a.txt", str(path)))
    assert content_of(service.requests[0]) == str(path).encode()


async def test_generated_chunks_are_streamed(fx: Flavor, service: Service) -> None:
    service.route = ok
    result = await fx.run(
        fx.client.index("acme/docs").put(
            "logs/big.log", chunks(50), metadata={"source": "job"}, if_none_match=True
        )
    )
    assert result.revision == "r1"
    request = service.requests[0]
    assert request.method == "PUT"
    assert request.url.path == "/v1/organizations/acme/indexes/docs/objects"
    assert request.headers["Transfer-Encoding"] == "chunked"
    assert request.headers["If-None-Match"] == "*"
    assert content_of(request) == b"".join(chunks(50))
    assert metadata_of(request) == {"source": {"type": "string", "value": "job"}}
    assert b'name="key"' in request.content and b"logs/big.log" in request.content


async def test_a_given_size_is_declared(fx: Flavor, service: Service) -> None:
    service.route = ok
    await fx.run(fx.client.index("acme/docs").put("big.bin", chunks(5), size=5000))
    request = service.requests[0]
    assert int(request.headers["Content-Length"]) == len(request.content)
    assert "Transfer-Encoding" not in request.headers
    assert content_of(request) == b"".join(chunks(5))


@pytest.mark.parametrize("size", [4999, 5001])
async def test_content_of_another_size_is_refused(fx: Flavor, service: Service, size: int) -> None:
    service.route = ok
    with pytest.raises(ValueError, match="size="):
        await fx.run(fx.client.index("acme/docs").put("big.bin", chunks(5), size=size))


async def test_a_pipe_is_streamed_once(fx: Flavor, service: Service) -> None:
    service.route = ok
    read, write = os.pipe()
    os.write(write, b"piped data")
    os.close(write)
    with os.fdopen(read, "rb") as pipe:
        await fx.run(fx.client.index("acme/docs").put("p.txt", pipe))
    assert content_of(service.requests[0]) == b"piped data"
    assert service.requests[0].headers["Transfer-Encoding"] == "chunked"


async def test_chunks_must_be_bytes(fx: Flavor, service: Service) -> None:
    service.route = ok
    with pytest.raises(TypeError, match="must be bytes, not str"):
        await fx.run(fx.client.index("acme/docs").put("a.txt", iter(["text"])))


async def test_a_stream_is_not_retried_after_an_error_answer(fx: Flavor, service: Service) -> None:
    service.reply(error(503, "unavailable"), httpx.Response(200, json=MUTATION))
    with pytest.raises(grepvine.ServerError):
        await fx.run(fx.client.index("acme/docs").put("a.bin", chunks(3)))
    assert len(service.requests) == 1


async def test_a_stream_is_not_retried_after_a_connection_failure(
    fx: Flavor, service: Service
) -> None:
    service.reply(httpx.ConnectError("refused"), httpx.Response(200, json=MUTATION))
    with pytest.raises(grepvine.TransportError, match="cannot be sent again"):
        await fx.run(fx.client.index("acme/docs").put("a.bin", chunks(3)))
    assert len(service.requests) == 1  # one attempt, no retry


async def test_content_in_memory_is_retried(fx: Flavor, service: Service) -> None:
    service.reply(error(503, "unavailable"), httpx.Response(200, json=MUTATION))
    await fx.run(fx.client.index("acme/docs").put("a.bin", b"\x00\x01"))
    assert [content_of(request) for request in service.requests] == [b"\x00\x01"] * 2


async def test_async_chunks_need_an_async_client(service: Service) -> None:
    with pytest.raises(TypeError, match="AsyncClient"):
        grepvine.Client(trust_env=False).index("acme/docs").put("a", async_chunks(1))  # type: ignore[arg-type]


async def test_async_client_streams_async_chunks(service: Service) -> None:
    service.route = ok
    transport = httpx.MockTransport(service.handle)
    async with grepvine.AsyncClient(api_key="k", trust_env=False, transport=transport) as c:
        await c.index("acme/docs").put("big.bin", async_chunks(20), size=20_000)
    request = service.requests[0]
    assert content_of(request) == b"".join(chunks(20))
    assert int(request.headers["Content-Length"]) == len(request.content)


async def test_put_many_reads_documents_one_batch_at_a_time(fx: Flavor, service: Service) -> None:
    produced: list[int] = []
    seen: list[int] = []

    def documents() -> Iterator[grepvine.DocumentInput]:
        for n in range(3000):
            produced.append(n)
            yield {"key": f"{n}", "content": "x"}

    def answer(request: httpx.Request) -> httpx.Response:
        seen.append(len(produced))
        return httpx.Response(200, json={"results": [MUTATION] * request.content.count(b"\n")})

    service.route = answer
    results = await fx.run(fx.client.index("acme/docs").put_many(documents()))
    assert len(results) == 3000
    # The first request went out after 2,049 documents were read: one batch and one ahead.
    assert seen == [2049, 3000]


async def test_put_many_refuses_binary_content(fx: Flavor) -> None:
    with pytest.raises(
        ValueError, match="'b.bin' is not UTF-8 text; store binary content with put"
    ):
        await fx.run(
            fx.client.index("acme/docs").put_many([{"key": "b.bin", "content": b"\xff\xfe"}])
        )


async def test_put_many_failure_on_a_generator_names_the_document_read_ahead(
    fx: Flavor, service: Service
) -> None:
    def answer_first(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"results": [MUTATION] * request.content.count(b"\n")})

    service.reply(answer_first, error(413, "too_large"))
    documents = ({"key": f"{n}", "content": "x"} for n in range(5000))
    with pytest.raises(grepvine.PartialBatchError) as raised:
        await fx.run(fx.client.index("acme/docs").put_many(documents))
    assert len(raised.value.committed) == 2048
    assert raised.value.failed_keys == tuple(f"{n}" for n in range(2048, 4096))
    assert raised.value.pending_keys == ("4096",)
    assert next(documents)["key"] == "4097"
