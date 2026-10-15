"""Store documents, search them with a metadata filter, and delete the demo index."""

import argparse
import os
import uuid

import grepvine
from grepvine.models import CreateIndexRequest, QueryRequest, QueryRequestMode


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--keep-index", action="store_true", help="keep the demo index after the example"
    )
    args = parser.parse_args()
    organization = os.environ.get("GREPVINE_ORGANIZATION")
    if not organization:
        parser.error("set GREPVINE_ORGANIZATION")

    with grepvine.Client(
        api_key=os.environ["GREPVINE_API_KEY"],
        endpoint=os.environ.get("GREPVINE_API_ENDPOINT", "https://api.grepvine.ai"),
    ) as client:
        name = f"example-python-{uuid.uuid4().hex[:8]}"
        client.indexes.create(
            organization, body=CreateIndexRequest(name=name, description="Python SDK example")
        )
        client.indexes.wait_until_ready(organization, name)
        print(f"Created index {organization}/{name}")
        try:
            results = client.documents.put_many(
                organization,
                name,
                [
                    {
                        "key": "docs/welcome.txt",
                        "content": "hello from the Python SDK\n",
                        "metadata": {"kind": "guide"},
                    },
                    {
                        "key": "docs/reference.txt",
                        "content": "hello from the reference guide\n",
                        "metadata": {"kind": "guide"},
                    },
                    {
                        "key": "notes/todo.txt",
                        "content": "hello from a personal note\n",
                        "metadata": {"kind": "note"},
                    },
                ],
            )
            # Each document has its own result.
            for result in results:
                if result.error:
                    raise RuntimeError(f"{result.key} was not stored: {result.error.error}")
            print(f"Stored {len(results)} documents")

            print('Search: literal "hello"')
            literal = QueryRequest(pattern="hello", mode=QueryRequestMode.LITERAL)
            hits = list(
                grepvine.paginate(
                    client.search.query, organization=organization, index=name, body=literal
                )
            )
            for hit in hits:
                print(f"  {hit.key}:{hit.line_number}: {hit.text.rstrip()}")
            print("Search: literal \"hello\", filtered by kind = 'guide'")
            literal.filter_ = "kind = 'guide'"
            filtered = list(
                grepvine.paginate(
                    client.search.query, organization=organization, index=name, body=literal
                )
            )
            print(f"Found {len(hits)} matches and {len(filtered)} filtered matches")
            if len(hits) != 3 or len(filtered) != 2:
                raise RuntimeError(f"Expected 3 and 2 matches, got {len(hits)} and {len(filtered)}")
        finally:
            if args.keep_index:
                print(f"Kept index {organization}/{name}")
            else:
                client.indexes.delete(organization, name)
                print(f"Deletion requested for {organization}/{name}")


if __name__ == "__main__":
    main()
