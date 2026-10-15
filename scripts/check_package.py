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
import asyncio
import importlib.util
import json
import httpx
import grepvine_sdk
from grepvine_sdk import AsyncClient, Client, NotFoundError, RetryPolicy
from grepvine_sdk.models import APIKey, IndexData, MutationResult, SearchResult, User
assert importlib.util.find_spec('grepvine_sdk.generated') is None
assert not hasattr(grepvine_sdk, 'AuthenticatedClient')
assert repr(grepvine_sdk.default_client) == '<grepvine_sdk.Client unresolved>'
INDEX = {
    'id': '00000000-0000-0000-0000-000000000001', 'organization': 'acme', 'name': 'docs',
    'canonical_id': 'c', 'description': '', 'tags': {}, 'state': 'ready',
    'document_count': 0, 'content_bytes': 0, 'created_at': '2026-01-01T00:00:00Z',
}
def handler(request):
    assert request.headers['Authorization'] == 'Bearer gvk'
    path = request.url.path
    if path == '/v1/organizations/acme/indexes/docs':
        return httpx.Response(200, json=INDEX)
    if path.endswith('objects:batch'):
        record = json.loads(request.content.decode().strip())
        assert record['metadata']['kind'] == {'type': 'string', 'value': 'guide'}
        assert record['metadata']['path'] == {'type': 'string', 'value': 'a'}
        return httpx.Response(200, json={'results': [{'key': 'a', 'revision': 'r1'}]})
    if path.endswith('/query'):
        return httpx.Response(200, json={
            'results': [], 'pagination': {'has_next': False, 'next_page_id': ''}
        })
    return httpx.Response(404, json={'code': 'not_found', 'reason': 'resource', 'error': 'no'})
options = {'api_key': 'gvk', 'endpoint': 'https://example.test', 'env': {}}
documents = [{'key': 'a', 'content': 'hello', 'metadata': {'kind': 'guide'}}]
with Client(transport=httpx.MockTransport(handler), retry=RetryPolicy(), **options) as client:
    index = client.indexes.get('acme/docs')
    assert isinstance(index.data, IndexData)
    [result] = index.documents.put(documents)
    assert isinstance(result, MutationResult) and result.revision == 'r1'
    assert list(index.search('hello')) == []
    assert client.http.get('/organizations/acme/indexes/docs').json()['name'] == 'docs'
    try:
        client.organizations.get('missing')
    except NotFoundError as exc:
        assert exc.code == 'not_found'
    else:
        raise SystemExit('expected NotFoundError')
async def check_async():
    async with AsyncClient(transport=httpx.MockTransport(handler), **options) as client:
        index = await client.indexes.get('acme/docs')
        assert (await index.documents.put(documents))[0].revision == 'r1'
        assert [hit async for hit in index.search('hello')] == []
asyncio.run(check_async())
print('Installed wheel sync and async client requests passed')
""",
            ],
            cwd=directory,
            check=True,
        )


if __name__ == "__main__":
    main()
