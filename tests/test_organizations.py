from __future__ import annotations

import json
import uuid

import httpx
import pytest

from grepvine import (
    APIKey,
    APIKeyCreated,
    AuthenticationError,
    ConflictError,
    Member,
    NotFoundError,
    Organization,
)
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


async def test_create_delete_and_transfer(fx: Flavor, fake: FakeGrepvine) -> None:
    created = await fx.run(fx.client.organizations.create("acme"))
    assert isinstance(created, Organization)
    assert (created.name, created.role) == ("acme", "owner")
    with pytest.raises(ConflictError):
        await fx.run(fx.client.organizations.create("ACME"))

    fake.accounts.add_member("acme", "alice", "owner")
    fake.accounts.add_member("acme", "bob", "developer")
    await fx.run(fx.client.organizations.transfer_ownership("acme", "bob"))
    roles = {name: entry["role"] for name, entry in fake.accounts.members["acme"].items()}
    assert roles == {"alice": "admin", "bob": "owner"}
    assert json.loads(fake.requests[-1].content) == {"user": "bob"}

    fake.add_index("acme/docs")
    await fx.run(fx.client.organizations.delete("acme"))
    assert fake.requests[-1].method == "DELETE"
    with pytest.raises(NotFoundError):
        await fx.run(fx.client.organizations.get("acme"))


async def test_members(fx: Flavor, fake: FakeGrepvine) -> None:
    fake.add_organization("acme")
    fake.accounts.add_member("acme", "alice", "owner")
    fake.accounts.add_user("bob", "bob@example.com", "a long password")
    members = fx.client.organizations.members("acme")
    assert repr(members) == ("<AsyncMembers acme>" if fx.is_async else "<Members acme>")

    added = await fx.run(members.add("bob", "reader"))
    assert isinstance(added, Member)
    assert (added.user.name, added.role) == ("bob", "reader")
    listed = await fx.collect(members.list())
    assert [(member.user.name, member.role) for member in listed] == [
        ("alice", "owner"),
        ("bob", "reader"),
    ]
    assert [m.user.name for m in await fx.collect(members.list(limit=1))] == ["alice"]

    updated = await fx.run(members.update("bob", "admin"))
    assert updated.role == "admin"
    with pytest.raises(ValueError, match="ownership is transferred"):
        await fx.run(members.update("bob", "owner"))
    with pytest.raises(ValueError, match="role must be one of"):
        await fx.run(members.add("carol", "guest"))

    await fx.run(members.remove("bob"))
    assert [m.user.name for m in await fx.collect(members.list())] == ["alice"]
    with pytest.raises(NotFoundError):
        await fx.run(members.remove("bob"))


async def test_api_keys(fx: Flavor, fake: FakeGrepvine) -> None:
    created = await fx.run(fx.client.api_keys.create("ci"))
    assert isinstance(created, APIKeyCreated)
    assert created.key.startswith("gvk_")
    assert created.key not in repr(created)
    assert created.prefix == created.key[:12]

    listed = await fx.collect(fx.client.api_keys.list())
    assert [(key.id, key.name, key.revoked) for key in listed] == [(created.id, "ci", False)]
    assert isinstance(listed[0], APIKey)

    # The new key authenticates on its own.
    other = type(fx.client)(
        api_key=created.key,
        endpoint=fx.client.config.endpoint,
        env={},
        transport=httpx.MockTransport(fake.handle),
    )
    assert (await fx.run(other.account.me())).name == "alice"

    await fx.run(fx.client.api_keys.revoke(created.id))
    [revoked] = await fx.collect(fx.client.api_keys.list())
    assert revoked.revoked
    assert revoked.revoked_at is not None
    with pytest.raises(AuthenticationError):
        await fx.run(other.account.me())
    with pytest.raises(ValueError, match="not an API key id"):
        await fx.run(fx.client.api_keys.revoke("nonsense"))
    with pytest.raises(NotFoundError):
        await fx.run(fx.client.api_keys.revoke(uuid.uuid4()))
    with pytest.raises(ValueError, match="1 to 128"):
        await fx.run(fx.client.api_keys.create(""))
