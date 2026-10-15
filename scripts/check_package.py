"""Check an installed wheel independently of the source-tree editable package."""

import subprocess
import tomllib
from pathlib import Path
from tempfile import TemporaryDirectory

PACKAGE = Path(__file__).resolve().parents[1]


def main() -> None:
    project = tomllib.loads((PACKAGE / "pyproject.toml").read_text())["project"]
    wheel = PACKAGE / "dist" / f"grepvine-{project['version']}-py3-none-any.whl"
    with TemporaryDirectory(prefix="grepvine-wheel-") as directory:
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
import grepvine
from grepvine import AsyncClient, Client, NotFoundError, RetryPolicy, paginate
from grepvine.models import Index, IndexSummary, MutationResult, QueryRequest
assert importlib.util.find_spec('grepvine.generated') is None
assert not hasattr(grepvine, 'AuthenticatedClient')
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
    if path == '/v1/organizations/acme/indexes':
        return httpx.Response(200, json={
            'results': [INDEX], 'pagination': {'has_next': False, 'next_page_id': ''}
        })
    if path.endswith('objects:batch'):
        assert request.headers['Idempotency-Key']
        record = json.loads(request.content.decode().strip())
        assert record['metadata']['kind'] == {'type': 'string', 'value': 'guide'}
        assert record['metadata']['path'] == {'type': 'string', 'value': 'a'}
        return httpx.Response(200, json={'results': [{'key': 'a', 'revision': 'r1'}]})
    if path.endswith('/query'):
        return httpx.Response(200, json={
            'results': [], 'pagination': {'has_next': False, 'next_page_id': ''}
        })
    return httpx.Response(404, json={'code': 'not_found', 'reason': 'resource', 'error': 'no'})
options = {'api_key': 'gvk', 'endpoint': 'https://example.test'}
documents = [{'key': 'a', 'content': 'hello', 'metadata': {'kind': 'guide'}}]
query = QueryRequest(pattern='hello')
with Client(transport=httpx.MockTransport(handler), retry=RetryPolicy(), **options) as client:
    assert isinstance(client.indexes.wait_until_ready('acme', 'docs'), Index)
    [summary] = paginate(client.indexes.list, organization='acme')
    assert isinstance(summary, IndexSummary)
    [result] = client.documents.put_many('acme', 'docs', documents)
    assert isinstance(result, MutationResult) and result.revision == 'r1'
    assert list(paginate(client.search.query, organization='acme', index='docs', body=query)) == []
    assert client.http.get('/organizations/acme/indexes/docs').json()['name'] == 'docs'
    try:
        client.organizations.get('missing')
    except NotFoundError as exc:
        assert exc.code == 'not_found'
    else:
        raise SystemExit('expected NotFoundError')
async def check_async():
    async with AsyncClient(transport=httpx.MockTransport(handler), **options) as client:
        assert (await client.indexes.get('acme', 'docs')).name == 'docs'
        assert (await client.documents.put_many('acme', 'docs', documents))[0].revision == 'r1'
        hits = paginate(client.search.query, organization='acme', index='docs', body=query)
        assert [hit async for hit in hits] == []
asyncio.run(check_async())
print('Installed wheel sync and async client requests passed')
""",
            ],
            cwd=directory,
            check=True,
        )


if __name__ == "__main__":
    main()
