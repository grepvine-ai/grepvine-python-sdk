"""Ingest documents, search them with a metadata filter, and clean up the demo index."""

import argparse
import json
import os
import time
import uuid
from io import BytesIO
from typing import TypeVar

import httpx

from grepvine_sdk import UNSET, AuthenticatedClient, File, Response, Unset
from grepvine_sdk.generated.api.indexes import create_index, delete_index, get_index
from grepvine_sdk.generated.api.objects import put_document, put_objects
from grepvine_sdk.generated.api.search import query_index
from grepvine_sdk.generated.models import (
    CreateIndexRequest,
    Error,
    Index,
    IndexState,
    MutationBatchResult,
    MutationResult,
    PutDocumentForm,
    QueryPage,
    QueryRequest,
    QueryRequestMode,
)

T = TypeVar("T")


def result(response: Response[T | Error], expected: type[T]) -> T:
    if not 200 <= response.status_code < 300 or not isinstance(response.parsed, expected):
        raise RuntimeError(f"HTTP {response.status_code}: {response.parsed}")
    return response.parsed


def search(client: AuthenticatedClient, organization: str, index: str, filter_: str | None) -> int:
    request = QueryRequest(pattern="hello", mode=QueryRequestMode.LITERAL)
    if filter_ is not None:
        request.filter_ = filter_
    count = 0
    # Keep the request unchanged and follow continuation tokens until has_next is false.
    token: str | Unset = UNSET
    while True:
        response = result(
            query_index.sync_detailed(
                organization,
                index,
                client=client,
                body=request,
                amount=1,
                page=token,
            ),
            QueryPage,
        )
        for hit in response.results:
            print(f"  {hit.key}:{hit.line_number}: {hit.text.rstrip()}")
            count += 1
        if not response.pagination.has_next:
            return count
        token = response.pagination.next_page_id


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--keep-index", action="store_true", help="keep the demo index after the example"
    )
    args = parser.parse_args()
    api_key = os.environ.get("GREPVINE_API_KEY")
    organization = os.environ.get("GREPVINE_ORGANIZATION")
    if not api_key or not organization:
        parser.error("set GREPVINE_API_KEY and GREPVINE_ORGANIZATION")
    endpoint = os.environ.get("GREPVINE_API_ENDPOINT", "https://api.grepvine.ai").rstrip("/")
    if not endpoint.endswith("/v1"):
        endpoint += "/v1"
    index = "example-python-" + uuid.uuid4().hex[:8]

    with AuthenticatedClient(base_url=endpoint, token=api_key, timeout=httpx.Timeout(30)) as client:
        result(
            create_index.sync_detailed(
                organization,
                client=client,
                body=CreateIndexRequest(name=index),
            ),
            Index,
        )
        print(f"Created index {organization}/{index}")
        try:
            deadline = time.monotonic() + 30
            while (
                result(get_index.sync_detailed(organization, index, client=client), Index).state
                != IndexState.READY
            ):
                if time.monotonic() >= deadline:
                    raise RuntimeError("The demo index did not become ready within 30 seconds")
                time.sleep(0.1)

            # A single document uses multipart content and JSON-encoded typed metadata.
            single = result(
                put_document.sync_detailed(
                    organization,
                    index,
                    client=client,
                    idempotency_key=str(uuid.uuid4()),
                    body=PutDocumentForm(
                        key="docs/welcome.txt",
                        content=File(
                            payload=BytesIO(b"hello from the Python SDK\n"), file_name="welcome.txt"
                        ),
                        metadata=json.dumps({"kind": {"type": "string", "value": "guide"}}),
                    ),
                ),
                MutationResult,
            )
            if isinstance(single.error, Error) or not single.revision:
                raise RuntimeError(f"Document was not stored: {single}")

            # Batch ingestion sends one JSON record per line as raw UTF-8 NDJSON.
            records = [
                {
                    "key": "docs/reference.txt",
                    "content": "hello from the reference guide\n",
                    "metadata": {"kind": {"type": "string", "value": "guide"}},
                },
                {
                    "key": "notes/todo.txt",
                    "content": "hello from a personal note\n",
                    "metadata": {"kind": {"type": "string", "value": "note"}},
                },
            ]
            body = "".join(json.dumps(record) + "\n" for record in records).encode("utf-8")
            batch = result(
                put_objects.sync_detailed(
                    organization,
                    index,
                    client=client,
                    idempotency_key=str(uuid.uuid4()),
                    body=File(payload=BytesIO(body)),
                ),
                MutationBatchResult,
            )
            # A successful HTTP response can still contain failed individual documents.
            for item in batch.results:
                if isinstance(item.error, Error) or not item.revision:
                    raise RuntimeError(f"Document was not stored: {item}")
            print(f"Ingested {1 + len(batch.results)} documents")

            print('Search: literal "hello"')
            matches = search(client, organization, index, None)
            print(f"Found {matches} matches")
            print("Search: literal \"hello\", filtered by kind = 'guide'")
            filtered = search(client, organization, index, "kind = 'guide'")
            print(f"Found {filtered} filtered matches")
            if matches != 3 or filtered != 2:
                raise RuntimeError(
                    f"Expected 3 matches and 2 filtered matches, got {matches} and {filtered}"
                )
        finally:
            if args.keep_index:
                print(f"Kept index {organization}/{index}")
            else:
                deleted = delete_index.sync_detailed(organization, index, client=client)
                if deleted.status_code != 202:
                    raise RuntimeError(f"Could not delete demo index: {deleted.parsed}")
                print(f"Deletion requested for {organization}/{index}")


if __name__ == "__main__":
    main()
