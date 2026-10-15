"""Ingest documents, search them with a metadata filter, and clean up the demo index."""

import argparse
import os
import uuid

import grepvine_sdk


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--keep-index", action="store_true", help="keep the demo index after the example"
    )
    args = parser.parse_args()
    organization = os.environ.get("GREPVINE_ORGANIZATION")
    if not organization:
        parser.error("set GREPVINE_ORGANIZATION")

    # The endpoint and API key come from GREPVINE_API_ENDPOINT and GREPVINE_API_KEY, or from
    # ~/.grepvine/config.yaml as written by `gv login`.
    with grepvine_sdk.Client() as client:
        ref = f"{organization}/example-python-{uuid.uuid4().hex[:8]}"
        index = client.indexes.create(ref, description="Python SDK example", wait=True)
        print(f"Created index {index.ref}")
        try:
            documents = index.documents
            documents.put(
                "docs/welcome.txt", "hello from the Python SDK\n", metadata={"kind": "guide"}
            )
            results = documents.put(
                [
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
                ]
            )
            # Each document of a list write has its own result.
            for result in results:
                if not result.ok:
                    raise RuntimeError(f"{result.key} was not stored: {result.error}")
            print(f"Stored {1 + len(results)} documents")

            print('Search: literal "hello", one result per page')
            matches = 0
            for page in index.search("hello", regex=False, page_size=1).pages():
                for hit in page.results:
                    print(f"  {hit.key}:{hit.line_number}: {hit.text.rstrip()}")
                    matches += 1
            print("Search: literal \"hello\", filtered by kind = 'guide'")
            filtered = list(index.search("hello", regex=False, filter="kind = 'guide'"))
            print(f"Found {matches} matches and {len(filtered)} filtered matches")
            if matches != 3 or len(filtered) != 2:
                raise RuntimeError(f"Expected 3 and 2 matches, got {matches} and {len(filtered)}")
        finally:
            if args.keep_index:
                print(f"Kept index {index.ref}")
            else:
                index.delete()
                print(f"Deletion requested for {index.ref}")


if __name__ == "__main__":
    main()
