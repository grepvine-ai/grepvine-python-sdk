from __future__ import annotations

import json

import pytest

from grepvine_sdk import InvalidPageError, InvalidRequestError, SearchResult
from tests.conftest import Flavor
from tests.fake_server import FakeGrepvine

pytestmark = pytest.mark.anyio


@pytest.fixture
async def index(fx: Flavor, fake: FakeGrepvine):
    fake.add_index("acme/docs")
    index = await fx.run(fx.client.indexes.get("acme/docs"))
    await fx.run(
        index.documents.put(
            [
                {"key": "a.txt", "content": "hello world\nfoo bar\nhello again\n"},
                {"key": "b/c.txt", "content": "Hello there\nsecond line"},
                {"key": "img.bin", "content": b"\xff\xfehello"},
            ]
        )
    )
    fake.requests.clear()
    return index


async def test_regex_search_yields_results_with_offsets(
    fx: Flavor, fake: FakeGrepvine, index
) -> None:
    results = await fx.collect(index.search("hel+o"))

    assert [(r.key, r.line_number) for r in results] == [("a.txt", 1), ("a.txt", 3)]
    first = results[0]
    assert isinstance(first, SearchResult)
    assert first.text == "hello world"
    assert first.matches[0].offset == 0
    assert first.match_spans() == [(0, 5)]
    assert first.match_texts() == ["hello"]
    assert results[1].line_start_offset == len("hello world\nfoo bar\n")
    assert results[1].match_byte_spans() == [(0, 5)]
    request = fake.requests[-1]
    assert request.method == "POST"
    assert request.url.path.endswith("/indexes/docs/query")
    assert request.url.params["amount"] == "200"
    assert json.loads(request.content) == {"pattern": "hel+o"}


async def test_literal_and_case_insensitive_search(fx: Flavor, fake: FakeGrepvine, index) -> None:
    assert await fx.collect(index.search("hel+o", regex=False)) == []
    assert json.loads(fake.requests[-1].content) == {"pattern": "hel+o", "mode": "literal"}

    results = await fx.collect(index.search("hello", case_sensitive=False))
    assert [r.key for r in results] == ["a.txt", "a.txt", "b/c.txt"]
    assert json.loads(fake.requests[-1].content) == {"pattern": "hello", "case_sensitive": False}

    results = await fx.collect(index.search("hello", regex=False, whole_word=True))
    assert len(results) == 2
    assert json.loads(fake.requests[-1].content)["whole_word"] is True


async def test_whole_word_requires_literal_mode(fx: Flavor, fake: FakeGrepvine, index) -> None:
    with pytest.raises(ValueError, match="whole_word requires regex=False"):
        index.search("hello", whole_word=True)
    assert fake.requests == []


async def test_filters_restrict_by_metadata(fx: Flavor, fake: FakeGrepvine, index) -> None:
    results = await fx.collect(
        index.search("hello", case_sensitive=False, filters=["path STARTSWITH 'b/'", "size > 1"])
    )
    assert [r.key for r in results] == ["b/c.txt"]
    body = json.loads(fake.requests[-1].content)
    assert body["filter"] == "(path STARTSWITH 'b/') AND (size > 1)"

    results = await fx.collect(index.search("hello", filter="path = 'a.txt'"))
    assert [r.key for r in results] == ["a.txt", "a.txt"]
    assert json.loads(fake.requests[-1].content)["filter"] == "path = 'a.txt'"

    results = await fx.collect(index.search("hello", filters=["path = 'a.txt'"]))
    assert json.loads(fake.requests[-1].content)["filter"] == "path = 'a.txt'"

    with pytest.raises(ValueError, match="either filter or filters"):
        index.search("x", filter="a = 1", filters=["b = 2"])
    with pytest.raises(ValueError, match="empty expressions"):
        index.search("x", filters=[""])
    with pytest.raises(InvalidRequestError) as excinfo:
        await fx.collect(index.search("hello", filter="this is not valid"))
    assert excinfo.value.code == "invalid_filter"


async def test_context_lines(fx: Flavor, fake: FakeGrepvine, index) -> None:
    [result] = await fx.collect(index.search("foo", lines_before=1, lines_after=5))
    assert [(line.line_number, line.text) for line in result.lines_before] == [(1, "hello world")]
    assert [(line.line_number, line.text) for line in result.lines_after] == [
        (3, "hello again"),
        (4, ""),
    ]
    assert json.loads(fake.requests[-1].content) == {
        "pattern": "foo",
        "lines_before": 1,
        "lines_after": 5,
    }
    with pytest.raises(ValueError, match="between 0 and 20"):
        index.search("x", lines_after=21)


async def test_multiline_search_spans_lines(fx: Flavor, fake: FakeGrepvine, index) -> None:
    [result] = await fx.collect(index.search(r"bar\nhello", multiline=True))
    assert (result.line_number, result.last_line_number) == (2, 3)
    assert result.text == "foo bar\nhello again"
    assert result.lines == ["foo bar", "hello again"]
    assert result.numbered_lines() == [(2, "foo bar"), (3, "hello again")]
    assert result.match_texts() == ["bar\nhello"]
    assert json.loads(fake.requests[-1].content)["multiline"] is True


async def test_pagination_resends_the_same_body_and_survives_empty_pages(
    fx: Flavor, fake: FakeGrepvine, index
) -> None:
    fake.search_truncate_after = 1

    pages = await fx.collect(index.search("hello", page_size=200).pages())

    results = [r for page in pages for r in page.results]
    assert [(r.key, r.line_number) for r in results] == [("a.txt", 1), ("a.txt", 3)]
    assert any(page.results == () and page.has_next for page in pages)
    assert pages[-1].has_next is False
    assert len({request.content for request in fake.requests}) == 1
    assert {request.url.params["amount"] for request in fake.requests} == {"200"}

    fake.requests.clear()
    assert [r.line_number for r in await fx.collect(index.search("hello"))] == [1, 3]


async def test_limit_and_page_size(fx: Flavor, fake: FakeGrepvine, index) -> None:
    results = await fx.collect(index.search("hello", limit=1))
    assert len(results) == 1
    assert fake.requests[-1].url.params["amount"] == "1"

    assert await fx.collect(index.search("hello", limit=0)) == []
    assert len(fake.requests) == 1

    with pytest.raises(ValueError, match="page_size"):
        index.search("hello", page_size=0)
    with pytest.raises(ValueError, match="limit"):
        index.search("hello", limit=-1)
    with pytest.raises(ValueError, match="pattern"):
        index.search("")


async def test_page_token_bound_to_arguments(fx: Flavor, fake: FakeGrepvine, index) -> None:
    [first, *_] = await fx.collect(index.search("hello", page_size=1).pages())
    assert first.has_next
    assert first.next_page_id

    resumed = await fx.collect(index.search("hello", page=first.next_page_id, page_size=1))
    assert [r.line_number for r in resumed] == [3]

    with pytest.raises(InvalidPageError) as excinfo:
        await fx.collect(index.search("hello", page=first.next_page_id, page_size=2))
    assert excinfo.value.code == "invalid_page"
    assert isinstance(excinfo.value, InvalidRequestError)


async def test_invalid_pattern_is_reported(fx: Flavor, index) -> None:
    with pytest.raises(InvalidRequestError) as excinfo:
        await fx.collect(index.search("(unclosed"))
    assert excinfo.value.code == "invalid_pattern"


async def test_paginator_is_reiterable_and_lazy(fx: Flavor, fake: FakeGrepvine, index) -> None:
    paginator = index.search("hello")
    assert fake.requests == []
    assert paginator.page_size == 200
    assert paginator.limit is None
    assert "query" in repr(paginator)
    first = await fx.collect(paginator)
    second = await fx.collect(paginator)
    assert [r.line_number for r in first] == [r.line_number for r in second] == [1, 3]
    assert (await fx.run(paginator.first())).line_number == 1
    assert await fx.run(index.search("zzz").first()) is None
