"""The ingest and search example with the asynchronous client."""

import asyncio
import os
import uuid

import grepvine_sdk


async def main() -> None:
    organization = os.environ["GREPVINE_ORGANIZATION"]
    async with grepvine_sdk.AsyncClient() as client:
        ref = f"{organization}/example-python-async-{uuid.uuid4().hex[:8]}"
        index = await client.indexes.create(ref, wait=True)
        print(f"Created index {index.ref}")
        try:
            await index.documents.put(
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
            async for hit in index.search("hello", regex=False, filter="kind = 'guide'"):
                print(f"  {hit.key}:{hit.line_number}: {hit.text.rstrip()}")
            listed = [doc.key async for doc in index.documents.list(prefix="docs/")]
            print(f"Documents under docs/: {listed}")
        finally:
            await index.delete()
            print(f"Deletion requested for {index.ref}")


if __name__ == "__main__":
    asyncio.run(main())
