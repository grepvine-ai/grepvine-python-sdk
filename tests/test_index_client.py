"""IndexClient: one index's operations, bound to its organization and name."""

from __future__ import annotations

import io
import json
from datetime import UTC, datetime

import httpx
import pytest

import grepvine
from grepvine.models import DocumentSummary, IndexState, QueryResult
from tests.conftest import Flavor, Service, index_json, page_json

pytestmark = pytest.mark.anyio

HIT = {
    "key": "src/a.go",
    "revision": "r1",
    "line_number": 3,
    "last_line_number": 3,
    "line_start_offset": 0,
    "line_end_offset": 11,
    "text_start_offset": 0,
    "text_line_number": 3,
    "text": "// TODO fix",
    "matches": [],
    "text_truncated": False,
    "matches_truncated": False,
}
MUTATION = {"key": "a.md", "revision": "r2", "status": "created"}


def document(key: str) -> dict[str, object]:
    return {
        "key": key,
        "revision": "r1",
        "content_bytes": 1,
        "searchable": True,
        "updated_at": "2026-01-02T03:04:05Z",
        "metadata": {},
    }


def test_making_one_sends_no_request(service: Service) -> None:
    with grepvine.Client(transport=httpx.MockTransport(service.handle)) as client:
        index = client.index("acme/docs")
    assert index.name == "acme/docs" and repr(index) == "IndexClient('acme/docs')"
    assert service.requests == []


@pytest.mark.parametrize("name", ["docs", "acme/", "/docs", "acme/docs/x"])
def test_bad_names_are_refused(name: str) -> None:
    with pytest.raises((ValueError, grepvine.ConfigurationError)):
        grepvine.Client(use_environment=False).index(name)


async def test_query_follows_pages_and_sends_only_given_options(
    fx: Flavor, service: Service
) -> None:
    service.reply(
        httpx.Response(200, json=page_json([HIT], "p2")),
        httpx.Response(200, json=page_json([HIT])),
    )
    hits = fx.client.index("acme/docs").query(
        pattern="TODO", mode="literal", filter=None, lines_after=2
    )
    assert service.requests == []
    found = await fx.collect(hits)
    assert [type(hit) for hit in found] == [QueryResult, QueryResult]
    assert [request.url.path for request in service.requests] == [
        "/v1/organizations/acme/indexes/docs/query"
    ] * 2
    sent = service.json(0)
    assert sent["mode"] == "literal" and sent["lines_after"] == 2
    assert "filter" not in sent
    assert service.requests[1].url.params["page"] == "p2"


async def test_query_page(fx: Flavor, service: Service) -> None:
    service.reply(httpx.Response(200, json=page_json([HIT], "p2")))
    page = await fx.run(
        fx.client.index("acme/docs").query_page(pattern="x", filter="path STARTSWITH 'src/'")
    )
    assert page.pagination.next_page_id == "p2"
    assert service.json(0)["filter"] == "path STARTSWITH 'src/'"


async def test_put_takes_bytes_text_or_a_file_with_plain_metadata(
    fx: Flavor, service: Service
) -> None:
    service.route = lambda request: httpx.Response(200, json=MUTATION)
    index = fx.client.index("acme/docs")
    stamp = datetime(2026, 10, 1, tzinfo=UTC)
    await fx.run(index.put("a.md", "hello", metadata={"source": "export", "at": stamp}))
    await fx.run(index.put("b.bin", b"\x00\x01", if_none_match=True))
    await fx.run(index.put("c.csv", io.BytesIO(b"a,b\n"), if_match="r1"))
    first, second, third = service.requests
    assert first.method == "PUT" and first.url.path.endswith("/indexes/docs/objects")
    assert b"hello" in first.content
    part = first.content.split(b'name="metadata"')[1].split(b"\r\n\r\n", 1)[1].split(b"\r\n")[0]
    metadata = json.loads(part)
    assert metadata["source"] == {"type": "string", "value": "export"}
    assert metadata["at"]["type"] == "timestamp"
    assert datetime.fromisoformat(metadata["at"]["value"]) == stamp
    assert second.headers["If-None-Match"] == "*" and b"\x00\x01" in second.content
    assert third.headers["If-Match"] == "r1" and b"a,b\n" in third.content


async def test_put_many_batches_through_the_index(fx: Flavor, service: Service) -> None:
    service.route = lambda request: httpx.Response(200, json={"results": [MUTATION]})
    results = await fx.run(
        fx.client.index("acme/docs").put_many(
            [{"key": "a.md", "content": "x"}], idempotency_key="import-2026-10-14-x"
        )
    )
    assert [result.revision for result in results] == ["r2"]
    request = service.requests[0]
    assert request.url.path == "/v1/organizations/acme/indexes/docs/objects:batch"
    assert request.headers["Idempotency-Key"] == "import-2026-10-14-x-0"


async def test_list_yields_prefixes_then_documents(fx: Flavor, service: Service) -> None:
    service.reply(
        httpx.Response(
            200,
            json=page_json([document("tickets/a.md")], "p2")
            | {"common_prefixes": ["tickets/2026/"]},
        ),
        httpx.Response(200, json=page_json([document("tickets/b.md")]) | {"common_prefixes": []}),
    )
    entries = await fx.collect(fx.client.index("acme/docs").list(prefix="tickets/", delimiter="/"))
    assert entries[0] == grepvine.Prefix("tickets/2026/")
    assert [entry.key for entry in entries[1:]] == ["tickets/a.md", "tickets/b.md"]
    assert all(isinstance(entry, DocumentSummary) for entry in entries[1:])
    assert dict(service.requests[1].url.params) == {
        "amount": "50",
        "prefix": "tickets/",
        "delimiter": "/",
        "page": "p2",
    }


async def test_get_delete_and_delete_batch(fx: Flavor, service: Service) -> None:
    service.reply(
        httpx.Response(206, content=b"func Refund()"),
        httpx.Response(200, json=MUTATION),
        httpx.Response(200, json={"results": [MUTATION, MUTATION]}),
    )
    index = fx.client.index("acme/docs")
    got = await fx.run(index.get("services/refund.go", range="bytes=0-12"))
    assert got.payload.read() == b"func Refund()"
    await fx.run(index.delete("a.md", if_match="r1"))
    await fx.run(index.delete_batch(objects=[{"key": "a.md"}, {"key": "b.md"}]))
    get, delete, batch = service.requests
    assert get.headers["Range"] == "bytes=0-12"
    assert get.url.path == "/v1/organizations/acme/indexes/docs/objects/services/refund.go"
    assert delete.method == "DELETE" and delete.headers["If-Match"] == "r1"
    assert service.json(2) == {"objects": [{"key": "a.md"}, {"key": "b.md"}]}


async def test_create_wait_update_and_delete_the_index(fx: Flavor, service: Service) -> None:
    service.reply(
        httpx.Response(201, json=index_json(state="creating")),
        httpx.Response(200, json=index_json(state="creating")),
        httpx.Response(200, json=index_json()),
        httpx.Response(200, json=index_json()),
        httpx.Response(202),
    )
    index = fx.client.index("acme/docs")
    created = await fx.run(index.create(description="# Docs", tags={"team": "search"}))
    assert created.state == IndexState.CREATING
    ready = await fx.run(index.wait_until_ready())
    assert ready.state == IndexState.READY
    await fx.run(index.update(tags={"team": None, "commit": "3f9c2a1"}))
    assert await fx.run(index.delete_index()) is None
    assert service.json(0) == {"name": "docs", "description": "# Docs", "tags": {"team": "search"}}
    assert service.requests[0].url.path == "/v1/organizations/acme/indexes"
    assert service.json(3) == {"tags": {"team": None, "commit": "3f9c2a1"}}
    assert service.requests[4].method == "DELETE"
    assert service.requests[4].url.path == "/v1/organizations/acme/indexes/docs"


async def test_info(fx: Flavor, service: Service) -> None:
    service.reply(httpx.Response(200, json=index_json()))
    info = await fx.run(fx.client.index("acme/docs").info())
    assert isinstance(info, grepvine.models.Index) and info.name == "docs"
