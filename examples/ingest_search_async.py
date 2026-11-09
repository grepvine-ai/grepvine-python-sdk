"""The ingest and search example with the asynchronous client."""

import asyncio
import uuid

import grepvine


async def main() -> None:
    async with grepvine.AsyncClient() as client:
        index = client.index(f"example-python-async-{uuid.uuid4().hex[:8]}")
        creation = await index.create()
        await creation.wait_until_ready()
        print(f"Created index {index.name}")
        try:
            await index.put_many(
                [
                    {
                        "key": "docs/welcome.txt",
                        "content": "hello\n",
                        "metadata": {"kind": "guide"},
                    },
                    {
                        "key": "notes/todo.txt",
                        "content": "hello again\n",
                        "metadata": {"kind": "note"},
                    },
                ]
            )
            hits = index.search(pattern="hello", mode="literal", filter="kind = 'guide'")
            async for hit in hits:
                print(f"  {hit.key}:{hit.line_number}: {hit.text.rstrip()}")
            listed = [entry async for entry in index.list(prefix="docs/")]
            print(f"Under docs/: {listed}")
        finally:
            await index.delete_index()
            print(f"Deletion requested for {index.name}")


if __name__ == "__main__":
    asyncio.run(main())
