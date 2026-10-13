"""Run the asynchronous convenience API against a configured Grepvine service."""

import asyncio
import os
import uuid

from grepvine_sdk import AsyncGrepvineClient


async def main() -> None:
    ref = f"{os.environ['GREPVINE_ORGANIZATION']}/convenience-async-{uuid.uuid4().hex[:8]}"
    async with AsyncGrepvineClient(
        api_key=os.environ["GREPVINE_API_KEY"],
        endpoint=os.environ.get("GREPVINE_API_ENDPOINT", "https://api.grepvine.ai"),
    ) as client:
        index = await client.indexes.create(ref)
        print(f"Created index {ref}")
        try:
            await index.wait_ready()
            await index.documents.put(
                "docs/welcome.txt", "hello from the async SDK\n", metadata={"kind": "guide"}
            )
            await index.documents.put_many(
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
            hits = [hit async for hit in index.search("hello", literal=True, amount=1)]
            filtered = [
                hit
                async for hit in index.search(
                    "hello", literal=True, filter="kind = 'guide'", amount=1
                )
            ]
            for hit in hits:
                print(f"  {hit.key}:{hit.line_number}: {hit.text.rstrip()}")
            print(f"Found {len(hits)} matches and {len(filtered)} filtered matches")
            if len(hits) != 3 or len(filtered) != 2:
                raise RuntimeError("Unexpected search results")
        finally:
            await index.delete()
            print(f"Deletion requested for {ref}")


if __name__ == "__main__":
    asyncio.run(main())
