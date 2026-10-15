"""The ingest and search example with the asynchronous client."""

import asyncio
import os
import uuid

import grepvine
from grepvine.models import CreateIndexRequest, QueryRequest, QueryRequestMode


async def main() -> None:
    organization = os.environ["GREPVINE_ORGANIZATION"]
    async with grepvine.AsyncClient(
        api_key=os.environ["GREPVINE_API_KEY"],
        endpoint=os.environ.get("GREPVINE_API_ENDPOINT", "https://api.grepvine.ai"),
    ) as client:
        name = f"example-python-async-{uuid.uuid4().hex[:8]}"
        await client.indexes.create(organization, body=CreateIndexRequest(name=name))
        await client.indexes.wait_until_ready(organization, name)
        print(f"Created index {organization}/{name}")
        try:
            await client.documents.put_many(
                organization,
                name,
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
                ],
            )
            query = QueryRequest(
                pattern="hello", mode=QueryRequestMode.LITERAL, filter_="kind = 'guide'"
            )
            async for hit in grepvine.paginate(
                client.search.query, organization=organization, index=name, body=query
            ):
                print(f"  {hit.key}:{hit.line_number}: {hit.text.rstrip()}")
            listed = [
                document.key
                async for document in grepvine.paginate(
                    client.documents.list, organization=organization, index=name, prefix="docs/"
                )
            ]
            print(f"Documents under docs/: {listed}")
        finally:
            await client.indexes.delete(organization, name)
            print(f"Deletion requested for {organization}/{name}")


if __name__ == "__main__":
    asyncio.run(main())
