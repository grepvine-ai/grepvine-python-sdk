from __future__ import annotations

import pytest

from grepvine_sdk import AsyncClient, Client, GrepvineError, Page
from grepvine_sdk._core.paging import (
    MAX_PAGE_SIZE,
    PageSource,
    resolve_page_size,
    validate_page_token,
)
from grepvine_sdk._generated.api.objects import list_documents
from grepvine_sdk._generated.models import DocumentPage
from tests.fake_server import API_KEY, FakeGrepvine


def _page(results: tuple[str, ...], token: str | None, page_size: int = 10) -> Page[str]:
    return Page(
        results=results, next_page_id=token, has_next=token is not None, page_size=page_size
    )


def _source(
    limit: int | None = None, start: str | None = None, page_size: int = 10
) -> PageSource[str]:
    return PageSource(
        operation=list_documents,
        page_model=DocumentPage,
        args=("acme", "docs"),
        kwargs={"prefix": "p"},
        page_size=page_size,
        limit=limit,
        start_page=start,
        parse_item=lambda data: str(data["v"]),
    )


def test_resolve_page_size_defaults() -> None:
    assert resolve_page_size(None, None) == MAX_PAGE_SIZE
    assert resolve_page_size(None, 5) == 5
    assert resolve_page_size(None, 500) == MAX_PAGE_SIZE
    assert resolve_page_size(None, 0) == MAX_PAGE_SIZE
    assert resolve_page_size(7, 5) == 7
    with pytest.raises(ValueError, match="limit"):
        resolve_page_size(None, -1)
    with pytest.raises(ValueError, match="page_size"):
        resolve_page_size(0, None)
    with pytest.raises(ValueError, match="page_size"):
        resolve_page_size(201, None)


def test_validate_page_token() -> None:
    assert validate_page_token(None) is None
    assert validate_page_token("") is None
    assert validate_page_token("abc") == "abc"
    with pytest.raises(ValueError, match="too long"):
        validate_page_token("x" * 4097)


def test_cursor_requests_constant_amount_and_follows_tokens() -> None:
    cursor = _source().cursor()
    spec = cursor.next_request()
    assert spec is not None
    assert spec.operation is list_documents
    assert spec.args == ("acme", "docs")
    assert spec.kwargs == {"prefix": "p", "amount": 10}

    assert cursor.feed(_page((), "t1")).results == ()
    spec = cursor.next_request()
    assert spec is not None
    assert spec.kwargs == {"prefix": "p", "amount": 10, "page": "t1"}

    cursor.feed(_page(("a",), None))
    assert cursor.next_request() is None


def test_cursor_clips_to_limit_and_stops() -> None:
    cursor = _source(limit=3).cursor()
    assert cursor.next_request() is not None
    page = cursor.feed(_page(("a", "b"), "t1"))
    assert page.results == ("a", "b")
    assert cursor.next_request() is not None
    page = cursor.feed(_page(("c", "d"), "t2"))
    assert page.results == ("c",)
    assert page.next_page_id == "t2"
    assert cursor.next_request() is None


def test_cursor_with_zero_limit_sends_nothing() -> None:
    assert _source(limit=0).cursor().next_request() is None


def test_cursor_starts_at_the_given_token() -> None:
    spec = _source(start="resume").cursor().next_request()
    assert spec is not None
    assert spec.kwargs["page"] == "resume"


def test_cursor_rejects_a_page_that_does_not_advance() -> None:
    cursor = _source().cursor()
    cursor.next_request()
    with pytest.raises(GrepvineError, match="did not advance"):
        cursor.feed(Page(results=(), next_page_id=None, has_next=True, page_size=10))
    cursor = _source(start="same").cursor()
    cursor.next_request()
    with pytest.raises(GrepvineError, match="did not advance"):
        cursor.feed(_page((), "same"))


def test_page_from_json_normalizes_tokens() -> None:
    page = Page._from_json(
        {"results": [{"v": 1}], "pagination": {"next_page_id": "", "has_next": False}},
        lambda d: d["v"],
        5,
    )
    assert page == Page(results=(1,), next_page_id=None, has_next=False, page_size=5)
    page = Page._from_json(
        {"results": [], "pagination": {"next_page_id": "t", "has_next": True}}, lambda d: d, 5
    )
    assert (page.next_page_id, page.has_next) == ("t", True)
    page = Page._from_json(
        {"results": [], "pagination": {"next_page_id": "t", "has_next": False}}, lambda d: d, 5
    )
    assert page.next_page_id is None
    page = Page._from_json({"results": [], "common_prefixes": ["a/"]}, lambda d: d, 5)
    assert page.common_prefixes == ("a/",)


def test_sync_paginator_rejects_async_iteration(client: Client, fake: FakeGrepvine) -> None:
    fake.add_organization("acme")
    with pytest.raises(TypeError, match="synchronous"):
        client.organizations.list().__aiter__()


@pytest.mark.anyio
async def test_async_paginator_rejects_sync_iteration(fake: FakeGrepvine) -> None:
    import httpx

    async with AsyncClient(
        api_key=API_KEY, endpoint="http://grepvine.test", transport=httpx.MockTransport(fake.handle)
    ) as client:
        with pytest.raises(TypeError, match="asynchronous"):
            list(client.organizations.list())
        assert "organizations" in repr(client.organizations.list())
