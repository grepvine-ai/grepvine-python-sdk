"""Check an installed wheel independently of the source-tree editable package."""

import hashlib
import subprocess
import tarfile
import tomllib
import zipfile
from email.parser import Parser
from pathlib import Path
from tempfile import TemporaryDirectory

PACKAGE = Path(__file__).resolve().parents[1]
# SHA-256 of https://www.apache.org/licenses/LICENSE-2.0.txt
APACHE_LICENSE_SHA256 = "cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30"


def check_license(project: dict, wheel: Path) -> None:
    """Fail unless the sources, wheel and sdist all carry Apache 2.0 with LICENSE and NOTICE."""
    license_text = (PACKAGE / "LICENSE").read_bytes()
    notice_text = (PACKAGE / "NOTICE").read_bytes()
    assert hashlib.sha256(license_text).hexdigest() == APACHE_LICENSE_SHA256, (
        "LICENSE is not the Apache License 2.0 text"
    )
    assert project["license"] == "Apache-2.0", project["license"]
    name = f"grepvine-{project['version']}"
    with zipfile.ZipFile(wheel) as archive:
        metadata = Parser().parsestr(archive.read(f"{name}.dist-info/METADATA").decode())
        assert metadata["License-Expression"] == "Apache-2.0", metadata["License-Expression"]
        assert sorted(metadata.get_all("License-File") or []) == ["LICENSE", "NOTICE"]
        assert archive.read(f"{name}.dist-info/licenses/LICENSE") == license_text
        assert archive.read(f"{name}.dist-info/licenses/NOTICE") == notice_text
    with tarfile.open(wheel.with_name(f"{name}.tar.gz")) as sdist:
        files = {}
        for member in ("PKG-INFO", "LICENSE", "NOTICE"):
            file = sdist.extractfile(f"{name}/{member}")
            assert file is not None, f"sdist is missing {member}"
            files[member] = file.read()
    metadata = Parser().parsestr(files["PKG-INFO"].decode())
    assert metadata["License-Expression"] == "Apache-2.0", metadata["License-Expression"]
    assert files["LICENSE"] == license_text
    assert files["NOTICE"] == notice_text


def main() -> None:
    project = tomllib.loads((PACKAGE / "pyproject.toml").read_text())["project"]
    wheel = PACKAGE / "dist" / f"grepvine-{project['version']}-py3-none-any.whl"
    check_license(project, wheel)
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
