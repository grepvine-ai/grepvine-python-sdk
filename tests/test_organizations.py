from __future__ import annotations

import pytest

from grepvine_sdk import NotFoundError, Organization
from tests.conftest import Flavor
from tests.fake_server import FakeGrepvine

pytestmark = pytest.mark.anyio


async def test_get_returns_the_organization(fx: Flavor, fake: FakeGrepvine) -> None:
    fake.add_organization("acme", role="admin")

    org = await fx.run(fx.client.organizations.get("acme"))

    assert isinstance(org, Organization)
    assert (org.name, org.role) == ("acme", "admin")
    assert org.created_at.year == 2026
    assert fake.requests[-1].url.path == "/v1/organizations/acme"


async def test_get_missing_raises_not_found(fx: Flavor, fake: FakeGrepvine) -> None:
    with pytest.raises(NotFoundError) as excinfo:
        await fx.run(fx.client.organizations.get("nope"))
    assert excinfo.value.status_code == 404
    assert excinfo.value.code == "not_found"
    assert excinfo.value.request_id == "req-1"
    assert str(excinfo.value).endswith("(not_found; request req-1)")


async def test_list_paginates_through_every_organization(fx: Flavor, fake: FakeGrepvine) -> None:
    for number in range(7):
        fake.add_organization(f"org-{number}")

    names = [org.name for org in await fx.collect(fx.client.organizations.list(page_size=3))]

    assert names == [f"org-{number}" for number in range(7)]
    amounts = [request.url.params["amount"] for request in fake.requests]
    assert amounts == ["3", "3", "3"]
    assert "page" not in fake.requests[0].url.params
    assert all("page" in request.url.params for request in fake.requests[1:])


async def test_list_honours_limit(fx: Flavor, fake: FakeGrepvine) -> None:
    for number in range(7):
        fake.add_organization(f"org-{number}")

    names = [org.name for org in await fx.collect(fx.client.organizations.list(limit=4))]

    assert names == ["org-0", "org-1", "org-2", "org-3"]
    assert len(fake.requests) == 1
    assert fake.requests[0].url.params["amount"] == "4"


async def test_pages_expose_continuation_tokens(fx: Flavor, fake: FakeGrepvine) -> None:
    for number in range(5):
        fake.add_organization(f"org-{number}")

    pages = await fx.collect(fx.client.organizations.list(page_size=2).pages())

    assert [len(page.results) for page in pages] == [2, 2, 1]
    assert [page.has_next for page in pages] == [True, True, False]
    assert pages[-1].next_page_id is None
    assert pages[0].page_size == 2

    resumed = await fx.collect(
        fx.client.organizations.list(page=pages[0].next_page_id, page_size=pages[0].page_size)
    )
    assert [org.name for org in resumed] == ["org-2", "org-3", "org-4"]
