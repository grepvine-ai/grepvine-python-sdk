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

import grepvine as grepvine

pytestmark = pytest.mark.integration

ENDPOINT = os.environ.get("GREPVINE_SDK_TEST_ENDPOINT")
API_KEY = os.environ.get("GREPVINE_SDK_TEST_API_KEY")
ORGANIZATION = os.environ.get("GREPVINE_SDK_TEST_ORGANIZATION")

if not (ENDPOINT and API_KEY and ORGANIZATION):
    pytest.skip(
        "set GREPVINE_SDK_TEST_ENDPOINT, GREPVINE_SDK_TEST_API_KEY and "
        "GREPVINE_SDK_TEST_ORGANIZATION to run the live tests",
        allow_module_level=True,
    )


@pytest.fixture(scope="module")
def client() -> Iterator[grepvine.Client]:
    with grepvine.Client(api_key=API_KEY, endpoint=ENDPOINT, env={}) as live:
        yield live


@pytest.fixture(scope="module")
def index(client: grepvine.Client) -> Iterator[grepvine.Index]:
    ref = f"{ORGANIZATION}/sdk-test-{uuid.uuid4().hex[:8]}"
    created = client.indexes.create(ref, exist_ok=True, wait=True)
    try:
        yield created
    finally:
        client.indexes.delete(ref)


def test_organization_is_visible(client: grepvine.Client) -> None:
    assert ORGANIZATION in [org.name for org in client.organizations.list()]
    assert client.organizations.get(ORGANIZATION).name == ORGANIZATION


def test_account_and_members(client: grepvine.Client) -> None:
    me = client.account.me()
    assert me.name
    assert ORGANIZATION
    members = list(client.organizations.members(ORGANIZATION).list())
    assert members
    assert all(member.role in {"owner", "admin", "developer", "reader"} for member in members)


def test_document_round_trip(client: grepvine.Client, index: grepvine.Index) -> None:
    assert index.exists()
    assert client.indexes.create(index.ref, exist_ok=True).ref == index.ref

    documents = index.documents
    single = documents.put("src/main.py", content=b"def main():\n    print('hello world')\n")
    results = documents.put(
        [
            {"key": "src/util.py", "content": "def helper():\n    return 'hello'\n"},
            {"key": "assets/logo.bin", "content": b"\x89PNG\r\n\x1a\n\x00"},
        ]
    )
    assert [result.key for result in results] == ["src/util.py", "assets/logo.bin"]
    assert all(result.ok and result.revision for result in results)
    [stale] = documents.put([{"key": "src/util.py", "content": "x", "if_match": "stale-revision"}])
    assert stale.error is not None
    assert stale.error.code == "precondition_failed"

    fetched = documents.fetch("src/main.py")
    assert fetched.revision == single.revision
    assert fetched.metadata["path"] == "src/main.py"
    assert fetched.metadata["size"] == fetched.size
    assert documents.get("src/main.py", mode="r").startswith("def main")
    assert documents.get("src/main.py", range=(0, 2)) == b"def"

    listed = list(documents.list(prefix="src/"))
    assert sorted(doc.key for doc in listed) == ["src/main.py", "src/util.py"]
    assert all(doc.searchable for doc in listed)
    [page] = list(documents.list(delimiter="/").pages())
    assert set(page.common_prefixes) == {"assets/", "src/"}
    assert not [doc for doc in documents.list(prefix="assets/") if doc.searchable]

    hits = list(index.search("hello", regex=False))
    assert sorted(hit.key for hit in hits) == ["src/main.py", "src/util.py"]
    filtered = list(index.search("hello", filters=["path STARTSWITH 'src/u'"]))
    assert [hit.key for hit in filtered] == ["src/util.py"]
    assert filtered[0].match_texts() == ["hello"]
    [main_hit] = list(index.search("print\\(", lines_before=1))
    assert main_hit.lines_before[0].text == "def main():"

    with pytest.raises(grepvine.PreconditionFailedError):
        documents.delete("src/main.py", if_match="stale-revision")
    documents.delete("src/main.py", if_match=fetched.revision)
    with pytest.raises(grepvine.NotFoundError):
        documents.get("src/main.py")
    deleted = documents.delete(["src/util.py", "assets/logo.bin", "never-existed"])
    assert [result.key for result in deleted] == ["src/util.py", "assets/logo.bin", "never-existed"]
    assert [result.ok for result in deleted] == [True, True, False]
    assert deleted[2].error is not None
    assert deleted[2].error.code == "not_found"
    assert list(documents.list()) == []
