"""Check an installed wheel independently of the source-tree editable package."""

import subprocess
import tomllib
from pathlib import Path
from tempfile import TemporaryDirectory

PACKAGE = Path(__file__).resolve().parents[1]


def main() -> None:
    project = tomllib.loads((PACKAGE / "pyproject.toml").read_text())["project"]
    wheel = PACKAGE / "dist" / f"grepvine_sdk-{project['version']}-py3-none-any.whl"
    with TemporaryDirectory(prefix="grepvine-sdk-wheel-") as directory:
        environment = Path(directory) / "venv"
        requirements = Path(directory) / "requirements.txt"
        subprocess.run(
            [
                "uv",
                "export",
                "--frozen",
                "--no-dev",
                "--no-emit-project",
                "--format",
                "requirements-txt",
                "--output-file",
                str(requirements),
            ],
            cwd=PACKAGE,
            check=True,
            stdout=subprocess.DEVNULL,
        )
        subprocess.run(["uv", "venv", str(environment)], check=True)
        python = environment / "bin/python"
        subprocess.run(
            ["uv", "pip", "sync", "--python", str(python), str(requirements)], check=True
        )
        subprocess.run(
            ["uv", "pip", "install", "--python", str(python), "--no-deps", str(wheel)], check=True
        )
        subprocess.run(
            [
                str(python),
                "-I",
                "-c",
                """
import pkgutil
import grepvine_sdk.generated.api as api
from grepvine_sdk import AuthenticatedClient, GrepvineClient, AsyncGrepvineClient
import asyncio
import httpx
import json
from grepvine_sdk.generated.api.objects import put_document, put_objects, get_document
from grepvine_sdk.generated.api.search import query_index
from grepvine_sdk.generated.models import QueryRequest, Metadata
assert {entry.name for entry in pkgutil.iter_modules(api.__path__)} == {
    'device_login', 'indexes', 'objects', 'search'
}
assert QueryRequest(pattern='hello').to_dict()['pattern'] == 'hello'
assert Metadata.from_dict({'n': {'type': 'integer', 'value': 123}}).to_dict()['n']['value'] == 123
with AuthenticatedClient(base_url='https://example.test/v1', token='gvk') as client:
    assert client.get_httpx_client().headers['Authorization'] == 'Bearer gvk'
def handler(request):
    assert request.headers['Authorization'] == 'Bearer gvk'
    if request.url.path.endswith('objects:batch'):
        record = json.loads(request.content.decode().strip())
        assert record['metadata']['kind'] == {'type': 'string', 'value': 'guide'}
        return httpx.Response(200, json={'results': [{'key': 'a', 'revision': 'r1'}]})
    return httpx.Response(200, json={
        'results': [], 'pagination': {'has_next': False, 'next_page_id': ''}
    })
options = {'api_key': 'gvk', 'httpx_args': {'transport': httpx.MockTransport(handler)}}
documents = [{'key': 'a', 'content': 'hello', 'metadata': {'kind': 'guide'}}]
with GrepvineClient(**options) as client:
    index = client.indexes.get('acme/docs')
    assert index.documents.put_many(documents)[0].revision == 'r1'
    assert list(index.search('hello')) == []
async def check_async():
    async with AsyncGrepvineClient(**options) as client:
        index = client.indexes.get('acme/docs')
        assert (await index.documents.put_many(documents))[0].revision == 'r1'
        assert [hit async for hit in index.search('hello')] == []
asyncio.run(check_async())
print('Installed wheel raw and sync/async convenience requests passed')
""",
            ],
            cwd=directory,
            check=True,
        )


if __name__ == "__main__":
    main()
