"""Run the synchronous convenience API against a configured Grepvine service."""

import os
import uuid

from grepvine_sdk import GrepvineClient


def main() -> None:
    ref = f"{os.environ['GREPVINE_ORGANIZATION']}/convenience-sync-{uuid.uuid4().hex[:8]}"
    with GrepvineClient(
        api_key=os.environ["GREPVINE_API_KEY"],
        endpoint=os.environ.get("GREPVINE_API_ENDPOINT", "https://api.grepvine.ai"),
    ) as client:
        index = client.indexes.create(ref)
        print(f"Created index {ref}")
        try:
            index.wait_ready()
            index.documents.put(
                "docs/welcome.txt", "hello from the sync SDK\n", metadata={"kind": "guide"}
            )
            index.documents.put_many(
                [
                    {
                        "key": "docs/reference.txt",
                        "content": "hello reference\n",
                        "metadata": {"kind": "guide"},
                    },
                    {
                        "key": "notes/todo.txt",
                        "content": "hello note\n",
                        "metadata": {"kind": "note"},
                    },
                ]
            )
            hits = list(index.search("hello", literal=True, amount=1))
            filtered = list(index.search("hello", literal=True, filter="kind = 'guide'", amount=1))
            for hit in hits:
                print(f"  {hit.key}:{hit.line_number}: {hit.text.rstrip()}")
            print(f"Found {len(hits)} matches and {len(filtered)} filtered matches")
            if len(hits) != 3 or len(filtered) != 2:
                raise RuntimeError("Unexpected search results")
        finally:
            index.delete()
            print(f"Deletion requested for {ref}")


if __name__ == "__main__":
    main()
