"""Store documents, search them with a metadata filter, and delete the demo index.

The client is configured like gv: GREPVINE_API_KEY, GREPVINE_API_ENDPOINT and
GREPVINE_ORGANIZATION, else ~/.grepvine/config.yaml.
"""

import argparse
import uuid

import grepvine


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--keep-index", action="store_true", help="keep the demo index after the example"
    )
    args = parser.parse_args()

    with grepvine.Client() as client:
        if not client.settings.organization:
            parser.error("set GREPVINE_ORGANIZATION, or gv config set organization")
        index = client.index(f"example-python-{uuid.uuid4().hex[:8]}")
        index.create(description="Python SDK example")
        index.wait_until_ready()
        print(f"Created index {index.name}")
        try:
            results = index.put_many(
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
                ]
            )
            # Each document has its own result.
            for result in results:
                if result.error:
                    raise RuntimeError(f"{result.key} was not stored: {result.error.error}")
            print(f"Stored {len(results)} documents")

            print('Search: literal "hello"')
            hits = list(index.query(pattern="hello", mode="literal"))
            for hit in hits:
                print(f"  {hit.key}:{hit.line_number}: {hit.text.rstrip()}")
            print("Search: literal \"hello\", filtered by kind = 'guide'")
            filtered = list(index.query(pattern="hello", mode="literal", filter="kind = 'guide'"))
            print(f"Found {len(hits)} matches and {len(filtered)} filtered matches")
            if len(hits) != 3 or len(filtered) != 2:
                raise RuntimeError(f"Expected 3 and 2 matches, got {len(hits)} and {len(filtered)}")
        finally:
            if args.keep_index:
                print(f"Kept index {index.name}")
            else:
                index.delete_index()
                print(f"Deletion requested for {index.name}")


if __name__ == "__main__":
    main()
