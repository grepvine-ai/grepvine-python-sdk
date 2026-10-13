"""Optional checks on a disposable index in a configured live service."""

import asyncio
import json
import os
import time
import uuid
from io import BytesIO

import pytest

from grepvine_sdk import AsyncGrepvineClient, AuthenticatedClient, File, GrepvineClient
from grepvine_sdk.generated.api.indexes import create_index, delete_index, get_index
from grepvine_sdk.generated.api.objects import (
    get_document,
    list_documents,
    put_document,
    put_objects,
)
from grepvine_sdk.generated.api.search import query_index
from grepvine_sdk.generated.models import (
    CreateIndexRequest,
    DocumentPage,
    Error,
    Index,
    MutationBatchResult,
    MutationResult,
    PutDocumentForm,
    QueryPage,
    QueryRequest,
)

ENDPOINT = os.environ.get("GREPVINE_SDK_TEST_ENDPOINT")
API_KEY = os.environ.get("GREPVINE_SDK_TEST_API_KEY")
ORGANIZATION = os.environ.get("GREPVINE_SDK_TEST_ORGANIZATION")


@pytest.mark.skipif(
    not (ENDPOINT and API_KEY and ORGANIZATION), reason="live SDK test configuration absent"
)
def test_live_round_trip() -> None:
    assert ENDPOINT and API_KEY and ORGANIZATION
    index = "sdk-python-" + uuid.uuid4().hex[:8]
    with AuthenticatedClient(base_url=ENDPOINT, token=API_KEY) as client:
        created = create_index.sync_detailed(
            ORGANIZATION, client=client, body=CreateIndexRequest(name=index)
        )
        assert created.status_code == 201, created.parsed
        try:
            deadline = time.monotonic() + 30
            while True:
                info = get_index.sync(ORGANIZATION, index, client=client)
                if isinstance(info, Index) and info.state.value == "ready":
                    break
                assert time.monotonic() < deadline, info
                time.sleep(0.1)
            key = "sdk/café %.txt"
            uploaded = put_document.sync(
                ORGANIZATION,
                index,
                client=client,
                idempotency_key=str(uuid.uuid4()),
                body=PutDocumentForm(
                    key=key,
                    content=File(BytesIO(b"hello world"), "hello.txt"),
                    metadata=json.dumps({"flag": {"type": "boolean", "value": True}}),
                ),
            )
            assert isinstance(uploaded, MutationResult), uploaded
            assert uploaded.revision
            body = (
                b'{"key":"sdk/b.txt","content":"hello again"}\n'
                b'{"key":"sdk/c.txt","content":"hello third"}\n'
            )
            batch = put_objects.sync(
                ORGANIZATION,
                index,
                client=client,
                idempotency_key=str(uuid.uuid4()),
                body=File(BytesIO(body)),
            )
            assert isinstance(batch, MutationBatchResult), batch
            assert len(batch.results) == 2
            assert all(result.revision for result in batch.results)
            downloaded = get_document.sync_detailed(
                ORGANIZATION, index, key, client=client, range_="bytes=0-4"
            )
            assert downloaded.status_code == 206
            assert downloaded.content == b"hello"
            assert downloaded.headers["ETag"] == uploaded.revision
            listed = list_documents.sync(
                ORGANIZATION, index, client=client, prefix="sdk/", amount=1
            )
            assert isinstance(listed, DocumentPage), listed
            assert len(listed.results) == 1 and listed.pagination.has_next
            continued = list_documents.sync(
                ORGANIZATION,
                index,
                client=client,
                prefix="sdk/",
                amount=1,
                page=listed.pagination.next_page_id,
            )
            assert isinstance(continued, DocumentPage), continued
            assert continued.results[0].key != listed.results[0].key

            filtered = query_index.sync(
                ORGANIZATION,
                index,
                client=client,
                body=QueryRequest(pattern="hello", filter_="flag = true"),
            )
            assert isinstance(filtered, QueryPage), filtered
            assert [result.key for result in filtered.results] == [key]

            async def search() -> None:
                assert ENDPOINT and API_KEY and ORGANIZATION
                async with AuthenticatedClient(base_url=ENDPOINT, token=API_KEY) as async_client:
                    first = await query_index.asyncio(
                        ORGANIZATION,
                        index,
                        client=async_client,
                        body=QueryRequest(pattern="hello"),
                        amount=1,
                    )
                    assert isinstance(first, QueryPage), first
                    assert len(first.results) == 1 and first.pagination.has_next
                    second = await query_index.asyncio(
                        ORGANIZATION,
                        index,
                        client=async_client,
                        body=QueryRequest(pattern="hello"),
                        amount=1,
                        page=first.pagination.next_page_id,
                    )
                    assert isinstance(second, QueryPage), second
                    assert second.results[0].key != first.results[0].key

            asyncio.run(search())
            missing = get_document.sync_detailed(ORGANIZATION, index, "missing", client=client)
            assert missing.status_code == 404 and isinstance(missing.parsed, Error)
            assert missing.parsed.code == "not_found"
        finally:
            assert delete_index.sync_detailed(ORGANIZATION, index, client=client).status_code == 202


@pytest.mark.skipif(
    not (ENDPOINT and API_KEY and ORGANIZATION), reason="live SDK test configuration absent"
)
@pytest.mark.parametrize("asynchronous", [False, True])
def test_convenience_round_trip(asynchronous: bool) -> None:
    assert ENDPOINT and API_KEY and ORGANIZATION
    ref = f"{ORGANIZATION}/sdk-convenience-{uuid.uuid4().hex[:8]}"
    if asynchronous:

        async def run() -> None:
            assert ENDPOINT and API_KEY
            async with AsyncGrepvineClient(api_key=API_KEY, endpoint=ENDPOINT) as client:
                index = await client.indexes.create(ref)
                try:
                    await index.wait_ready()
                    await index.documents.put("a", "hello one", metadata={"kind": "guide"})
                    await index.documents.put_many(
                        [
                            {"key": "b", "content": "hello two", "metadata": {"kind": "guide"}},
                            {"key": "c", "content": "hello three", "metadata": {"kind": "note"}},
                        ]
                    )
                    hits = [hit async for hit in index.search("hello", literal=True, amount=1)]
                    assert {hit.key for hit in hits} == {"a", "b", "c"}
                    filtered = [
                        hit
                        async for hit in index.search("hello", filter="kind = 'guide'", amount=1)
                    ]
                    assert {hit.key for hit in filtered} == {"a", "b"}
                finally:
                    await index.delete()

        asyncio.run(run())
    else:
        with GrepvineClient(api_key=API_KEY, endpoint=ENDPOINT) as client:
            index = client.indexes.create(ref)
            try:
                index.wait_ready()
                index.documents.put("a", "hello one", metadata={"kind": "guide"})
                index.documents.put_many(
                    [
                        {"key": "b", "content": "hello two", "metadata": {"kind": "guide"}},
                        {"key": "c", "content": "hello three", "metadata": {"kind": "note"}},
                    ]
                )
                assert {hit.key for hit in index.search("hello", literal=True, amount=1)} == {
                    "a",
                    "b",
                    "c",
                }
                assert {
                    hit.key for hit in index.search("hello", filter="kind = 'guide'", amount=1)
                } == {"a", "b"}
            finally:
                index.delete()
