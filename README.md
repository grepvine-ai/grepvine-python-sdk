# Grepvine generated Python SDK

The SDK includes all 34 public API operations: Authentication, Device login,
API keys, Organizations and membership, Indexes, Objects, and Search.
API keys authenticate operations that support bearer credentials; browser-account
operations use the session authentication described by the API contract.

Grepvine exports its full public contract as `spec/openapi.json` without filtering
operations or components. `spec/source.json` records the source repository,
commit, exported operation list, and snapshot checksum.

Typed synchronous and asynchronous operations for the Grepvine API, for Python 3.11+.
The distribution name is `grepvine-sdk`; its import name is `grepvine_sdk`.
It can coexist with the separate handwritten `grepvine` package.

## Installation

```sh
pip install grepvine-sdk
# or
uv add grepvine-sdk
```

The package requires Python 3.11 or later.

## Authentication

API keys authenticate the convenience clients and every operation that accepts
bearer credentials. Pass the key as `api_key` to `GrepvineClient` or
`AsyncGrepvineClient`, or as `token` to the generated `AuthenticatedClient`.
Clients do not read local configuration or environment variables automatically.
Browser-account operations use session authentication instead: use the
generated `Client`, configure its cookies, and supply the CSRF token through the
operation's `x_csrf_token` argument.

## Convenience API

Use `GrepvineClient` for synchronous calls and `AsyncGrepvineClient` for
asynchronous calls. Their methods handle request encoding, idempotency keys,
API errors, and search continuation.

```python
from grepvine_sdk import GrepvineClient

with GrepvineClient(api_key="gvk_your_api_key", endpoint="http://localhost:8080") as client:
    index = client.indexes.get("local/docs")
    index.documents.put("hello.txt", "hello world", metadata={"kind": "guide"})
    index.documents.put_many([
        {"key": "other.txt", "content": "hello again", "metadata": {"kind": "note"}},
    ])
    for hit in index.search("hello", literal=True, filter="kind = 'guide'"):
        print(hit.key, hit.text)
```

```python
from grepvine_sdk import AsyncGrepvineClient

async with AsyncGrepvineClient(api_key="gvk_your_api_key", endpoint="http://localhost:8080") as client:
    index = client.indexes.get("local/docs")
    await index.documents.put("hello.txt", "hello world", metadata={"kind": "guide"})
    await index.documents.put_many([{"key": "other.txt", "content": "hello again"}])
    async for hit in index.search("hello", literal=True):
        print(hit.key, hit.text)
```

`indexes.get("organization/index")` creates a handle without a request.
Use `index.info()` to fetch its current state. `indexes.create(ref,
description=..., tags=...)` creates an index; `index.wait_ready(timeout=30)`
polls until it is ready. `index.delete()` requests deletion. Await network
methods in async mode. Python context managers close the relevant HTTPX
client; `close()` / `aclose()` are also available.

`put` accepts text, bytes, or a binary file object. Caller-owned files remain
open. Metadata accepts strings, booleans, finite numbers and timezone-aware
`datetime` values; the wrapper supplies the API's type tags. `if_match` and
`if_none_match=True` provide write preconditions.

One `put_many` call sends **one batch**, up to 2,048 text documents and
16 MiB of UTF-8 content. It validates/encodes the complete batch before any
request. It does not split or retry automatically. Each write gets a new
idempotency key unless `idempotency_key=...` is supplied. Supply a stable key
and the same data when implementing retries.

`ApiError` exposes `status`, `code`, `reason`, `request_id`, `retry_after`
(seconds or None), and response headers. `BatchError` retains all `results`,
including successes, plus `failures` and `request_id`. Use
`raise_on_error=False` to receive batch results without raising on individual
failures. HTTPX transport exceptions and async cancellation propagate.

Search is a lazy sync/async iterator over the API's JSON responses, including
empty responses with a continuation token. It is regex by default; use
`literal=True`. Options include `filter`, `case_sensitive`, `whole_word`,
`multiline`, `lines_before`, `lines_after`, and `amount` (1–200).

After setting the environment variables shown below, run the complete examples:

```sh
uv run --frozen python examples/convenience_sync.py
uv run --frozen python examples/convenience_async.py
```

The generated `Client` and `AuthenticatedClient` exports remain unchanged.
`convenience_client.raw` is the generated authenticated client and can be
passed to any raw operation, including device-login operations.

## Raw generated API

```python
from grepvine_sdk import AuthenticatedClient
from grepvine_sdk.generated.api.search import query_index
from grepvine_sdk.generated.models import Error, QueryPage, QueryRequest

with AuthenticatedClient(
    base_url="https://api.grepvine.ai/v1",
    token="gvk_your_api_key",
) as client:
    response = query_index.sync_detailed(
        "acme", "notes", client=client, body=QueryRequest(pattern="hello")
    )
    if isinstance(response.parsed, Error):
        print(response.status_code, response.parsed, response.headers.get("X-Request-ID"))
    elif isinstance(response.parsed, QueryPage):
        print(response.parsed.results)
```

Each operation provides `sync`, `sync_detailed`, `asyncio`, and
`asyncio_detailed` functions when it has a response body.
The detailed variants expose HTTP status, headers, raw bytes, and the decoded
result. Declared API errors are decoded as `Error`, rather than raised.
Network/timeout errors are HTTPX exceptions. Always inspect the result.
For asynchronous use:

```python
async with AuthenticatedClient(base_url="https://api.grepvine.ai/v1", token="gvk_your_api_key") as client:
    response = await query_index.asyncio_detailed(
        "acme", "notes", client=client, body=QueryRequest(pattern="hello")
    )
```

Supply the full versioned API URL, including `/v1`. Credentials are per client.
Clients do not read local configuration or environment variables automatically.
Use `Client` for anonymous or session-authenticated operations. Configure
cookies on that client and supply the CSRF token on state changes using the
operation's `x_csrf_token` argument.

## Uploads, downloads, and continuation

```python
from io import BytesIO
import json
import uuid

from grepvine_sdk import File
from grepvine_sdk.generated.api.objects import put_document, put_objects
from grepvine_sdk.generated.models import PutDocumentForm

with AuthenticatedClient(base_url="https://api.grepvine.ai/v1", token="gvk_your_api_key") as client:
    single = put_document.sync_detailed(
        "acme", "notes", client=client, idempotency_key=str(uuid.uuid4()),
        body=PutDocumentForm(
            key="hello.txt",
            content=File(payload=BytesIO(b"hello"), file_name="hello.txt"),
            metadata=json.dumps({"lang": {"type": "string", "value": "en"}}),
        ),
    )
    records = [{"key": "other.txt", "content": "hello again"}]
    payload = "".join(json.dumps(record) + "\n" for record in records).encode("utf-8")
    batch = put_objects.sync_detailed(
        "acme", "notes", client=client, idempotency_key=str(uuid.uuid4()),
        body=File(payload=BytesIO(payload)),
    )
    print(batch.parsed)  # inspect every document result's error
```

Data mutations require an `idempotency_key`. When retrying, preserve that
key and the complete original body. The SDK does not retry automatically.
Detailed error responses expose `Retry-After` and `X-Request-ID`.

List/search operations return one response at a time. When
`pagination.has_next` is true, pass `pagination.next_page_id` as `page`,
preserving the original request. Pagination is explicit.
Generated models serialize tagged metadata and support full int64 values.
For updates, `UNSET` means absent; null tag values remove the named tags.

`get_document.sync_detailed` returns binary bytes in `response.content`
and a `File` in `response.parsed`, with revision/range/metadata headers in
`response.headers`. Generated download functions buffer the complete response.
For large downloads use `client.get_httpx_client().stream(...)` or
`client.get_async_httpx_client().stream(...)`, consuming chunks inside the
HTTPX stream context. Encode each path parameter using
`urllib.parse.quote(value, safe="")`. Configure timeouts with
`timeout=httpx.Timeout(seconds)`. Async task cancellation propagates through
HTTPX; context managers close connections.

Grepvine currently exposes no REST SSE operation. This package has no SSE
parser or generated streaming search function. Adding SSE requires a separate
API/server change and a tested synchronous/asynchronous streaming adapter.

## Generation and development

This package uses `openapi-python-client==0.29.1` with HTTPX and attrs models.
Hey API's Python generator was evaluated and rejected for this implementation
because its current operation generation does not correctly handle paths and
request arguments. Python users need neither Node.js nor the generator.

Generation reads `spec/openapi.json`. The script
temporarily expresses the `If-None-Match` constant as a singleton enum and
interprets the raw NDJSON body as a binary File. Both preserve wire behavior;
the original media type is retained. The snapshot is exported from Grepvine;
change the source contract there rather than editing the snapshot.
The raw-body template buffers NDJSON content into bytes so both sync and
async HTTPX clients can send it. Generation fails on warnings or missing operations.

Run from the SDK repository root:

```sh
uv sync --frozen
uv run --frozen python scripts/generate.py
uv run --frozen ruff check .
uv run --frozen ruff format --check .
uv run --frozen mypy
uv run --frozen pytest
uv build
uv run --frozen python scripts/check_package.py
```

Generated files live under `src/grepvine_sdk/generated`. Never edit them:
change the contract, configuration, or generator adapter and regenerate.
Exports, docs, tests, and scripts remain separate. Builds create a wheel
and source distribution with typing information and a license.
The distribution name is provisional until registry availability is checked before release.

The API documentation site is built with pdoc into the git-ignored `site/`
directory. Its landing page is this README without the development and
automation sections, followed by the reference for the convenience layer and
the generated operations and models. Any pdoc warning fails the build. Open
`site/index.html` in a browser to read the result:

```sh
uv run --frozen python scripts/build_docs.py
```

The theme lives in `docs/theme`: pdoc template and stylesheet overrides in
`templates/`, and a vendored copy of the Grepvine design system in
`design-system/` (see its `SOURCE.md` to refresh it).

Optional live tests create and delete a uniquely named index. Set
`GREPVINE_SDK_TEST_ENDPOINT` (including `/v1`), `GREPVINE_SDK_TEST_API_KEY`,
and `GREPVINE_SDK_TEST_ORGANIZATION`, then run `uv run --frozen pytest`.
The ordinary HTTP fixture tests require no running service.

## Runnable ingest and search example

The example creates a uniquely named index, stores one document with multipart
content and two documents in an NDJSON batch, then searches immediately. It
follows continuation tokens and demonstrates a metadata filter, returning
three matches overall and two matching `kind = 'guide'`.

After installing development dependencies, run from the repository root:

```sh
export GREPVINE_API_ENDPOINT=http://localhost:8080
export GREPVINE_ORGANIZATION=local
export GREPVINE_API_KEY='your-api-key'
uv run --frozen python examples/ingest_search.py
```

The example requests deletion of its own index in a `finally` block. Add
`--keep-index` to keep the documents for inspection.
The organization must already exist, and the key needs permission to create
and delete indexes. API endpoints may be supplied with or without `/v1`.

## Repository automation

The `Regenerate and validate SDK` workflow can be triggered manually. It
regenerates from the snapshot, runs tests and builds an installed-package
smoke test, then commits generated changes after the checks pass. Pushes and
pull requests validate reproducibility without committing. Grepvine’s manual `Update SDK snapshots` workflow
updates both repositories and requests regeneration.

The `Build and publish SDK` workflow runs the same checks, builds the wheel
and source distribution, and publishes them with PyPI trusted publishing.
Publishing a GitHub release uploads the tag's version (`v0.2.0` becomes
`0.2.0`) to PyPI. A manual run takes a version and a target index: use
`testpypi` to try any version on TestPyPI, or `pypi` for a pre-release
(`0.2.0rc1`, `0.2.0.dev1`), which `pip` installs only when asked for
explicitly or with `--pre`. Final versions go to PyPI only through a release.
Each index needs a trusted publisher for this repository, workflow
`publish.yml`, and a matching `pypi` or `testpypi` environment.

The `Documentation` workflow builds the API documentation on every pull request
and push to `main`, so a broken docstring reference fails CI. Publishing a
GitHub release, or running the workflow manually, also deploys the site to
GitHub Pages at the repository's default project URL. The site documents the
latest release only. Before the first deployment, set **Settings → Pages →
Source** to **GitHub Actions**; the workflow creates the `github-pages`
environment on its first run. The published site is public even when the
repository is private, and Pages on a private repository requires a paid
GitHub plan.
