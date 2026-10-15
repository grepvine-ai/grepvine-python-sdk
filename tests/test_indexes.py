from __future__ import annotations

import json
from typing import Any

import pytest

from grepvine import (
    AsyncIndex,
    Client,
    ConflictError,
    Index,
    InvalidRequestError,
    NotFoundError,
)
from tests.conftest import Flavor
from tests.fake_server import FakeGrepvine

pytestmark = pytest.mark.anyio


async def test_get_returns_a_handle_with_the_index_fields(fx: Flavor, fake: FakeGrepvine) -> None:
    fake.add_index("acme/docs")
    fake.add_document("acme/docs", "a.txt", "hello")

    index = await fx.run(fx.client.indexes.get("acme/docs"))

    assert index.ref == "acme/docs"
    assert (index.organization, index.name, index.state) == ("acme", "docs", "ready")
    assert index.document_count == 1
    assert index.content_bytes == 5
    assert index.canonical_id == index.id
    assert index.last_updated_at is None
    assert index.optimization_progress_percent is None
    assert repr(index).startswith(f"<{type(index).__name__} acme/docs state=ready documents=1>")
    assert index.data.ref == "acme/docs"


@pytest.mark.parametrize("ref", ["acme", "acme/", "/docs", "acme/docs/extra", ""])
async def test_get_rejects_malformed_references(fx: Flavor, ref: str) -> None:
    with pytest.raises(ValueError, match="ORGANIZATION/INDEX"):
        await fx.run(fx.client.indexes.get(ref))


async def test_get_missing_raises_not_found(fx: Flavor, fake: FakeGrepvine) -> None:
    fake.add_organization("acme")
    with pytest.raises(NotFoundError):
        await fx.run(fx.client.indexes.get("acme/nope"))


async def test_create_posts_the_name(fx: Flavor, fake: FakeGrepvine) -> None:
    fake.add_organization("acme")

    index = await fx.run(fx.client.indexes.create("acme/docs"))

    assert index.ref == "acme/docs"
    assert index.document_count == 0
    request = fake.requests[-1]
    assert (request.method, request.url.path) == ("POST", "/v1/organizations/acme/indexes")
    assert request.headers["content-type"] == "application/json"
    assert json.loads(request.content) == {"name": "docs"}
    assert ("acme", "docs") in fake.indexes


async def test_create_existing_raises_conflict(fx: Flavor, fake: FakeGrepvine) -> None:
    fake.add_index("acme/docs")
    with pytest.raises(ConflictError) as excinfo:
        await fx.run(fx.client.indexes.create("acme/docs"))
    assert excinfo.value.status_code == 409


async def test_create_exist_ok_returns_the_existing_index(fx: Flavor, fake: FakeGrepvine) -> None:
    fake.add_index("acme/docs")
    fake.add_document("acme/docs", "a.txt", "x")

    index = await fx.run(fx.client.indexes.create("acme/docs", exist_ok=True))

    assert index.document_count == 1
    assert [request.method for request in fake.requests] == ["POST", "GET"]


async def test_create_exist_ok_reraises_conflict_when_index_vanishes(
    fx: Flavor, fake: FakeGrepvine
) -> None:
    fake.add_organization("acme")
    fake.fail_next(409, code="conflict", message="taken", method="POST")

    with pytest.raises(ConflictError):
        await fx.run(fx.client.indexes.create("acme/docs", exist_ok=True))
    assert [request.method for request in fake.requests] == ["POST", "GET"]


async def test_delete_and_exists(fx: Flavor, fake: FakeGrepvine) -> None:
    fake.add_index("acme/docs")
    assert await fx.run(fx.client.indexes.exists("acme/docs")) is True

    await fx.run(fx.client.indexes.delete("acme/docs"))

    assert fake.requests[-1].method == "DELETE"
    assert await fx.run(fx.client.indexes.exists("acme/docs")) is False


async def test_delete_missing_raises_not_found(fx: Flavor, fake: FakeGrepvine) -> None:
    fake.add_organization("acme")
    with pytest.raises(NotFoundError):
        await fx.run(fx.client.indexes.delete("acme/nope"))


async def test_handle_methods_delegate_to_the_client(fx: Flavor, fake: FakeGrepvine) -> None:
    fake.add_index("acme/docs")
    index = await fx.run(fx.client.indexes.get("acme/docs"))
    assert await fx.run(index.exists()) is True

    fake.add_document("acme/docs", "a.txt", "x")
    refreshed = await fx.run(index.refresh())
    assert (index.document_count, refreshed.document_count) == (0, 1)

    await fx.run(index.delete())
    assert await fx.run(index.exists()) is False


async def test_list_yields_handles(fx: Flavor, fake: FakeGrepvine) -> None:
    fake.add_index("acme/a")
    fake.add_index("acme/b")
    fake.add_document("acme/b", "k", "12345")
    fake.add_index("other/c")

    indexes = await fx.collect(fx.client.indexes.list("acme"))

    assert [f"{index.name}: {index.document_count} documents" for index in indexes] == [
        "a: 0 documents",
        "b: 1 documents",
    ]
    expected = AsyncIndex if fx.is_async else Index
    assert all(isinstance(index, expected) for index in indexes)
    assert indexes[0].documents is not None


async def test_list_filters_by_prefix(fx: Flavor, fake: FakeGrepvine) -> None:
    for name in ("docs", "docs-v2", "notes"):
        fake.add_index(f"acme/{name}")

    indexes = await fx.collect(fx.client.indexes.list("acme", prefix="docs"))

    assert [index.name for index in indexes] == ["docs", "docs-v2"]
    assert fake.requests[-1].url.params["prefix"] == "docs"


def test_handles_compare_by_data(fake: FakeGrepvine, client: Client) -> None:
    fake.add_index("acme/docs")
    first = client.indexes.get("acme/docs")
    second = client.indexes.get("acme/docs")
    assert first == second
    assert hash(first) == hash(second)
    assert first != first.data
    fake.add_document("acme/docs", "a.txt", "x")
    assert first != client.indexes.get("acme/docs")


async def test_get_reports_the_description(fx: Flavor, fake: FakeGrepvine) -> None:
    fake.add_index("acme/docs", description="# Docs\n\nEvery *guide* we ship.")

    index = await fx.run(fx.client.indexes.get("acme/docs"))

    assert index.description == "# Docs\n\nEvery *guide* we ship."
    assert index.data.description == index.description


async def test_get_defaults_the_description_to_empty(fx: Flavor, fake: FakeGrepvine) -> None:
    fake.add_index("acme/docs")
    index = await fx.run(fx.client.indexes.get("acme/docs"))
    assert index.description == ""


async def test_create_sends_the_description_when_given(fx: Flavor, fake: FakeGrepvine) -> None:
    fake.add_organization("acme")

    index = await fx.run(fx.client.indexes.create("acme/docs", description="Guides."))

    assert index.description == "Guides."
    assert json.loads(fake.requests[-1].content) == {"description": "Guides.", "name": "docs"}
    assert fake.indexes[("acme", "docs")].description == "Guides."


async def test_create_exist_ok_keeps_the_existing_description(
    fx: Flavor, fake: FakeGrepvine
) -> None:
    fake.add_index("acme/docs", description="Original.")

    index = await fx.run(
        fx.client.indexes.create("acme/docs", description="Replacement.", exist_ok=True)
    )

    assert index.description == "Original."
    assert fake.indexes[("acme", "docs")].description == "Original."


async def test_update_replaces_the_description(fx: Flavor, fake: FakeGrepvine) -> None:
    fake.add_index("acme/docs", description="Original.")

    index = await fx.run(fx.client.indexes.update("acme/docs", description="Revised."))

    assert index.description == "Revised."
    request = fake.requests[-1]
    assert (request.method, request.url.path) == ("PATCH", "/v1/organizations/acme/indexes/docs")
    assert request.headers["content-type"] == "application/json"
    assert json.loads(request.content) == {"description": "Revised."}
    assert fake.indexes[("acme", "docs")].description == "Revised."

    cleared = await fx.run(fx.client.indexes.update("acme/docs", description=""))
    assert cleared.description == ""


async def test_handle_update_returns_a_new_handle(fx: Flavor, fake: FakeGrepvine) -> None:
    fake.add_index("acme/docs", description="Original.")
    index = await fx.run(fx.client.indexes.get("acme/docs"))

    updated = await fx.run(index.update(description="Revised."))

    assert (index.description, updated.description) == ("Original.", "Revised.")
    assert updated.ref == index.ref
    assert (await fx.run(index.refresh())).description == "Revised."


async def test_update_missing_raises_not_found(fx: Flavor, fake: FakeGrepvine) -> None:
    fake.add_organization("acme")
    with pytest.raises(NotFoundError):
        await fx.run(fx.client.indexes.update("acme/nope", description="x"))


async def test_create_checks_the_description_length_before_the_network(
    fx: Flavor, fake: FakeGrepvine
) -> None:
    fake.add_organization("acme")
    with pytest.raises(ValueError, match="16384"):
        await fx.run(fx.client.indexes.create("acme/new", description="x" * 16385))
    assert fake.requests == []


async def test_update_checks_the_description_length_before_the_network(
    fx: Flavor, fake: FakeGrepvine
) -> None:
    fake.add_index("acme/docs")
    with pytest.raises(ValueError, match="16384"):
        await fx.run(fx.client.indexes.update("acme/docs", description="x" * 16385))
    assert fake.requests == []


async def test_get_reports_the_tags(fx: Flavor, fake: FakeGrepvine) -> None:
    fake.add_index("acme/docs", tags={"team": "search", "commit": "3f9c2a1"})

    index = await fx.run(fx.client.indexes.get("acme/docs"))

    assert index.tags == {"team": "search", "commit": "3f9c2a1"}
    assert index.tags["commit"] == "3f9c2a1"
    assert dict(index.data.tags) == dict(index.tags)
    read_only: Any = index.tags
    with pytest.raises(TypeError):
        read_only["team"] = "platform"
    assert index.tags["team"] == "search"


async def test_get_defaults_the_tags_to_empty(fx: Flavor, fake: FakeGrepvine) -> None:
    fake.add_index("acme/docs")
    index = await fx.run(fx.client.indexes.get("acme/docs"))
    assert index.tags == {}
    assert index.data.tags == {}


async def test_create_sends_the_tags_when_given(fx: Flavor, fake: FakeGrepvine) -> None:
    fake.add_organization("acme")

    index = await fx.run(
        fx.client.indexes.create("acme/docs", tags={"team": "search", "commit": "3f9c2a1"})
    )

    assert index.tags == {"team": "search", "commit": "3f9c2a1"}
    assert json.loads(fake.requests[-1].content) == {
        "name": "docs",
        "tags": {"commit": "3f9c2a1", "team": "search"},
    }
    assert fake.indexes[("acme", "docs")].tags == {"team": "search", "commit": "3f9c2a1"}


async def test_create_without_tags_leaves_them_out_of_the_body(
    fx: Flavor, fake: FakeGrepvine
) -> None:
    fake.add_organization("acme")
    index = await fx.run(fx.client.indexes.create("acme/docs", description="Guides."))
    assert json.loads(fake.requests[-1].content) == {"description": "Guides.", "name": "docs"}
    assert index.tags == {}


async def test_create_exist_ok_keeps_the_existing_tags(fx: Flavor, fake: FakeGrepvine) -> None:
    fake.add_index("acme/docs", tags={"team": "search"})

    index = await fx.run(
        fx.client.indexes.create("acme/docs", tags={"team": "platform"}, exist_ok=True)
    )

    assert index.tags == {"team": "search"}
    assert fake.indexes[("acme", "docs")].tags == {"team": "search"}


async def test_update_merges_tags_and_removes_null_ones(fx: Flavor, fake: FakeGrepvine) -> None:
    fake.add_index(
        "acme/docs", description="Docs.", tags={"team": "search", "old": "gone", "keep": "me"}
    )

    index = await fx.run(
        fx.client.indexes.update(
            "acme/docs", tags={"team": "platform", "old": None, "commit": "3f9c2a1"}
        )
    )

    assert index.tags == {"team": "platform", "keep": "me", "commit": "3f9c2a1"}
    assert index.description == "Docs."
    request = fake.requests[-1]
    assert (request.method, request.url.path) == ("PATCH", "/v1/organizations/acme/indexes/docs")
    assert request.headers["content-type"] == "application/json"
    assert json.loads(request.content) == {
        "tags": {"commit": "3f9c2a1", "old": None, "team": "platform"}
    }
    assert fake.indexes[("acme", "docs")].tags == {
        "team": "platform",
        "keep": "me",
        "commit": "3f9c2a1",
    }
    assert fake.indexes[("acme", "docs")].description == "Docs."


async def test_update_with_only_a_description_leaves_tags_alone(
    fx: Flavor, fake: FakeGrepvine
) -> None:
    fake.add_index("acme/docs", tags={"team": "search"})

    index = await fx.run(fx.client.indexes.update("acme/docs", description="Revised."))

    assert json.loads(fake.requests[-1].content) == {"description": "Revised."}
    assert (index.description, index.tags) == ("Revised.", {"team": "search"})


async def test_update_sends_both_fields_when_both_are_given(fx: Flavor, fake: FakeGrepvine) -> None:
    fake.add_index("acme/docs")

    index = await fx.run(
        fx.client.indexes.update("acme/docs", description="Docs.", tags={"team": "search"})
    )

    assert json.loads(fake.requests[-1].content) == {
        "description": "Docs.",
        "tags": {"team": "search"},
    }
    assert (index.description, index.tags) == ("Docs.", {"team": "search"})


async def test_set_tags_and_remove_tags(fx: Flavor, fake: FakeGrepvine) -> None:
    fake.add_index("acme/docs", tags={"team": "search", "old": "gone"})
    index = await fx.run(fx.client.indexes.get("acme/docs"))

    tagged = await fx.run(index.set_tags({"commit": "3f9c2a1"}))

    assert tagged.tags == {"team": "search", "old": "gone", "commit": "3f9c2a1"}
    request = fake.requests[-1]
    assert (request.method, request.url.path) == ("PATCH", "/v1/organizations/acme/indexes/docs")
    assert json.loads(request.content) == {"tags": {"commit": "3f9c2a1"}}

    trimmed = await fx.run(tagged.remove_tags("old", "team"))

    assert trimmed.tags == {"commit": "3f9c2a1"}
    assert json.loads(fake.requests[-1].content) == {"tags": {"old": None, "team": None}}
    assert index.tags == {"team": "search", "old": "gone"}
    assert tagged.tags == {"team": "search", "old": "gone", "commit": "3f9c2a1"}


async def test_handle_tag_update_returns_a_new_handle(fx: Flavor, fake: FakeGrepvine) -> None:
    fake.add_index("acme/docs", tags={"team": "search"})
    index = await fx.run(fx.client.indexes.get("acme/docs"))

    updated = await fx.run(index.update(tags={"team": "platform"}))

    assert (index.tags, updated.tags) == ({"team": "search"}, {"team": "platform"})
    assert updated.ref == index.ref
    assert index != updated
    assert (await fx.run(index.refresh())).tags == {"team": "platform"}


async def test_update_with_nothing_to_change_raises_before_the_network(
    fx: Flavor, fake: FakeGrepvine
) -> None:
    fake.add_index("acme/docs")
    with pytest.raises(ValueError, match="nothing to change"):
        await fx.run(fx.client.indexes.update("acme/docs"))
    assert fake.requests == []

    index = await fx.run(fx.client.indexes.get("acme/docs"))
    with pytest.raises(ValueError, match="nothing to change"):
        await fx.run(index.update())
    assert [request.method for request in fake.requests] == ["GET"]


@pytest.mark.parametrize(
    "key", ["has space", "", "x" * 129, "tab\tkey", "ctl\x01", "line\nbreak", "nbsp\xa0"]
)
async def test_create_rejects_invalid_tag_keys_before_the_network(
    fx: Flavor, fake: FakeGrepvine, key: str
) -> None:
    fake.add_organization("acme")
    with pytest.raises(ValueError, match="tag key"):
        await fx.run(fx.client.indexes.create("acme/new", tags={key: "value"}))
    assert fake.requests == []


async def test_create_accepts_tags_at_the_limits(fx: Flavor, fake: FakeGrepvine) -> None:
    fake.add_organization("acme")
    tags = {f"k{i:02d}": "v" for i in range(63)} | {"k" * 128: "v" * 1024}

    index = await fx.run(fx.client.indexes.create("acme/docs", tags=tags))

    assert index.tags == tags
    assert len(index.tags) == 64


async def test_update_rejects_invalid_tags_before_the_network(
    fx: Flavor, fake: FakeGrepvine
) -> None:
    fake.add_index("acme/docs")
    with pytest.raises(ValueError, match="1024"):
        await fx.run(fx.client.indexes.update("acme/docs", tags={"key": "x" * 1025}))
    with pytest.raises(ValueError, match="whitespace"):
        await fx.run(fx.client.indexes.update("acme/docs", tags={"bad key": None}))
    with pytest.raises(ValueError, match="control"):
        await fx.run(fx.client.indexes.update("acme/docs", tags={"key": "line\nbreak"}))
    with pytest.raises(ValueError, match="64"):
        await fx.run(fx.client.indexes.update("acme/docs", tags={f"k{i}": "v" for i in range(65)}))
    with pytest.raises(ValueError, match="64"):
        await fx.run(fx.client.indexes.create("acme/new", tags={f"k{i}": "v" for i in range(65)}))
    not_a_string: Any = {"key": 1}
    with pytest.raises(TypeError, match="string"):
        await fx.run(fx.client.indexes.update("acme/docs", tags=not_a_string))
    with pytest.raises(TypeError, match="string"):
        await fx.run(fx.client.indexes.create("acme/new", tags=not_a_string))
    not_a_mapping: Any = [("key", "value")]
    with pytest.raises(TypeError, match="mapping"):
        await fx.run(fx.client.indexes.update("acme/docs", tags=not_a_mapping))
    with pytest.raises(TypeError, match="mapping"):
        await fx.run(fx.client.indexes.create("acme/new", tags=not_a_mapping))
    not_a_string_key: Any = {1: "value"}
    with pytest.raises(TypeError, match="tag keys"):
        await fx.run(fx.client.indexes.update("acme/docs", tags=not_a_string_key))
    assert fake.requests == []


async def test_update_that_exceeds_the_tag_limit_is_rejected_by_the_service(
    fx: Flavor, fake: FakeGrepvine
) -> None:
    fake.add_index("acme/docs", tags={f"k{i}": "v" for i in range(64)})
    with pytest.raises(InvalidRequestError) as excinfo:
        await fx.run(fx.client.indexes.update("acme/docs", tags={"one-more": "v"}))
    assert excinfo.value.status_code == 400
    assert len(fake.indexes[("acme", "docs")].tags) == 64
