"""Live checks against a real Grepvine deployment.

Set ``GREPVINE_SDK_TEST_ENDPOINT``, ``GREPVINE_SDK_TEST_API_KEY`` and
``GREPVINE_SDK_TEST_ORGANIZATION`` to run them. They create an index named
``sdk-test-<random>`` in that organization and delete it afterwards.
"""

from __future__ import annotations

import os
import uuid
from collections.abc import Iterator

import pytest

import grepvine
from grepvine.models import CreateIndexRequest, QueryRequest, QueryRequestMode

pytestmark = pytest.mark.integration

ENDPOINT = os.environ.get("GREPVINE_SDK_TEST_ENDPOINT", "")
API_KEY = os.environ.get("GREPVINE_SDK_TEST_API_KEY")
ORGANIZATION = os.environ.get("GREPVINE_SDK_TEST_ORGANIZATION", "")

if not (ENDPOINT and API_KEY and ORGANIZATION):
    pytest.skip(
        "set GREPVINE_SDK_TEST_ENDPOINT, GREPVINE_SDK_TEST_API_KEY and "
        "GREPVINE_SDK_TEST_ORGANIZATION to run the live tests",
        allow_module_level=True,
    )


@pytest.fixture(scope="module")
def client() -> Iterator[grepvine.Client]:
    with grepvine.Client(api_key=API_KEY, endpoint=ENDPOINT) as live:
        yield live


@pytest.fixture(scope="module")
def index(client: grepvine.Client) -> Iterator[str]:
    name = f"sdk-test-{uuid.uuid4().hex[:8]}"
    client.indexes.create(ORGANIZATION, body=CreateIndexRequest(name=name))
    try:
        client.indexes.wait_until_ready(ORGANIZATION, name)
        yield name
    finally:
        client.indexes.delete(ORGANIZATION, name)


def test_organization_and_account(client: grepvine.Client) -> None:
    names = [org.name for org in grepvine.paginate(client.organizations.list)]
    assert ORGANIZATION in names
    assert client.account.me().name


def test_store_list_and_search(client: grepvine.Client, index: str) -> None:
    documents: list[grepvine.DocumentInput] = [
        {"key": "docs/a.txt", "content": "hello live\n", "metadata": {"kind": "guide"}},
        {"key": "notes/b.txt", "content": "hello note\n", "metadata": {"kind": "note"}},
    ]
    results = client.documents.put_many(ORGANIZATION, index, documents)
    assert all(result.revision for result in results)
    listed = grepvine.paginate(client.documents.list, organization=ORGANIZATION, index=index)
    assert sorted(document.key for document in listed) == ["docs/a.txt", "notes/b.txt"]
    query = QueryRequest(pattern="hello", mode=QueryRequestMode.LITERAL, filter_="kind = 'guide'")
    hits = grepvine.paginate(
        client.search.query, organization=ORGANIZATION, index=index, body=query
    )
    assert [hit.key for hit in hits] == ["docs/a.txt"]
