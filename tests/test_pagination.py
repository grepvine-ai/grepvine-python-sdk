"""paginate follows next_page_id while has_next, through empty pages, for any list or search."""

from __future__ import annotations

import httpx
import pytest

import grepvine
from grepvine.models import IndexSummary, QueryRequest, QueryResult
from tests.conftest import Flavor, Service, index_json, page_json

pytestmark = pytest.mark.anyio


def summary(name: str) -> dict[str, object]:
    return index_json(name)


async def test_follows_pages_including_empty_ones(fx: Flavor, service: Service) -> None:
    service.reply(
        httpx.Response(200, json=page_json([summary("a"), summary("b")], "p2")),
        httpx.Response(200, json=page_json([], "p3")),
        httpx.Response(200, json=page_json([summary("c")])),
    )
    items = await fx.collect(
        grepvine.paginate(fx.client.indexes.list, organization="acme", prefix="x", amount=2)
    )
    assert all(isinstance(item, IndexSummary) for item in items)
    assert [item.name for item in items] == ["a", "b", "c"]
    params = [dict(request.url.params) for request in service.requests]
    assert params == [
        {"amount": "2", "prefix": "x"},
        {"amount": "2", "prefix": "x", "page": "p2"},
        {"amount": "2", "prefix": "x", "page": "p3"},
    ]


async def test_single_page(fx: Flavor, service: Service) -> None:
    service.reply(httpx.Response(200, json=page_json([])))
    assert await fx.collect(grepvine.paginate(fx.client.organizations.list)) == []
    assert len(service.requests) == 1


async def test_search_pages_resend_the_query(fx: Flavor, service: Service) -> None:
    hit = {
        "key": "a.txt",
        "revision": "r1",
        "line_number": 3,
        "last_line_number": 3,
        "line_start_offset": 0,
        "line_end_offset": 5,
        "text_start_offset": 0,
        "text_line_number": 3,
        "text": "hello",
        "matches": [],
        "text_truncated": False,
        "matches_truncated": False,
    }
    service.reply(
        httpx.Response(200, json=page_json([], "q2")),
        httpx.Response(200, json=page_json([hit])),
    )
    hits = await fx.collect(
        grepvine.paginate(
            fx.client.search.query,
            organization="acme",
            index="docs",
            body=QueryRequest(pattern="hel+o"),
        )
    )
    assert [type(hit) for hit in hits] == [QueryResult]
    assert hits[0].text == "hello"
    assert [service.json(n)["pattern"] for n in range(2)] == ["hel+o", "hel+o"]
    assert service.requests[1].url.params["page"] == "q2"


def test_sync_iterator_is_lazy(service: Service) -> None:
    service.route = lambda request: httpx.Response(200, json=page_json([summary("a")], "more"))
    with grepvine.Client(transport=httpx.MockTransport(service.handle)) as client:
        pages = grepvine.paginate(client.indexes.list, organization="acme")
        assert service.requests == []
        assert [next(pages).name, next(pages).name] == ["a", "a"]
    assert len(service.requests) == 2
