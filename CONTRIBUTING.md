# Contributing to the Grepvine Python SDK

`README.md` is the user guide and the landing page of the documentation site.
This file covers how the SDK is built, tested, documented and released.

## How the SDK is built

Most of the package is generated from the API contract by
`openapi-python-client==0.29.1`; a small hand-written part adds what a
generator cannot know.

### Generated

- `spec/openapi.json` is the full public contract, exported from
  `grepvine-ai/grepvine` without filtering operations or components.
  `spec/source.json` records the source repository, commit, the exported
  operation list, and the snapshot checksum. Change the contract in Grepvine,
  never the snapshot here.
- `sdk-operations.json` names the method of every operation: its value is the
  resource path and method name, in camelCase (`"putObjects": ["documents",
  "putBatch"]`). The TypeScript SDK (`grepvine-ai/grepvine-typescript-sdk`)
  holds an identical copy, so both SDKs name every method the same way;
  Python uses the snake_case form of each segment (`documents.put_batch`,
  `api_keys`). Generation fails when an operation of the contract has no
  entry, or an entry names an operation the contract lacks.
- `scripts/generate.py` runs the generator on the snapshot and writes the
  private package `src/grepvine/_generated`: the HTTPX transport, the attrs
  models, one module per operation with `sync_detailed` and
  `asyncio_detailed`, and `api/resources.py`. That module holds the resource
  classes (`Organizations` with `members`, `Indexes`, `Documents`, `Search`,
  `APIKeys`, `Account`, `DeviceLogin`, each with an `Async` twin) and the
  root classes `_GeneratedClient` and `_GeneratedAsyncClient`. The custom
  template `scripts/templates/api_init.py.jinja` renders them from the
  generator's `endpoint_collections_by_tag` and the naming map, which
  `generate.py` writes into the template directory as `sdk_resources.jinja`.
  Each method reuses the generator's own `arguments` and `docstring` macros,
  delegates to the operation's `sync_detailed` or `asyncio_detailed`, and
  returns the decoded model of a successful answer.
- The adapter in `generate.py` makes these changes before generating: the
  `If-None-Match` constant becomes a singleton enum; the NDJSON batch body
  becomes a binary `File` whose bytes the template buffers so both HTTPX
  clients can send it (the original media type is kept); `Idempotency-Key`
  becomes optional and the `X-Csrf-Token` header is dropped from the
  operations, because the client sends both itself; and the docstrings name
  the SDK's errors. Generation fails on generator warnings or a missing
  operation. Never edit `_generated` by hand: change the contract, the map,
  the generator configuration (`openapi-python-client.yaml`), the template or
  the adapter, and regenerate. Generating twice gives no diff.

### Hand-written

| Path | Contents |
| --- | --- |
| `src/grepvine/_client.py` | `Client` and `AsyncClient`, built on the root classes: options, bearer authentication, the session after `account.login`, the hook that raises errors, closing. |
| `src/grepvine/errors.py` | The exceptions, and `map_error`, the one function every error answer goes through. |
| `src/grepvine/_retry.py` | `RetryPolicy` and the retrying HTTPX transports, which also add the `Idempotency-Key` of every write. |
| `src/grepvine/_helpers.py` | `paginate`, and subclasses of three resource classes adding `indexes.wait_until_ready`, `documents.put_many` and `device_login.authorize`. |
| `src/grepvine/models.py` | Exports the models under their API names. |

Retries live in the HTTPX transport, so a retried request is the same
request, idempotency key included. The client's response hook maps every
error answer before the operation decodes it, so methods return only
successful answers. The helpers keep the names the TypeScript SDK uses
(`paginate`, `waitUntilReady`, `authorize`, `putMany`).

Loading the endpoint and API key from the environment or from `gv`'s
configuration file is deferred: the client uses only its arguments.

`tests/test_coverage.py` checks that `sdk-operations.json` names exactly the
operations of the contract and of `spec/source.json`, and that each one is a
method on both clients that calls that operation. When the API gains an
operation, generation and CI fail until the map has an entry.

## Development

Python users need neither Node.js nor the generator; contributors run
everything through `uv` from the repository root:

```sh
uv sync --frozen
uv run --frozen python scripts/generate.py   # then check `git status` shows no change
uv lock --check
uv run --frozen ruff check .
uv run --frozen ruff format --check .
uv run --frozen mypy
uv run --frozen pytest
uv build
uv run --frozen python scripts/check_package.py
uv run --frozen python scripts/build_docs.py
```

The tests answer requests with `httpx.MockTransport` from a scripted service
(`tests/conftest.py`), so they need no network, and a fake clock replaces
sleeping. Most tests run once with `Client` and once with `AsyncClient`
through the `fx` fixture. Warnings are errors.

Optional live tests in `tests/test_live.py` create and delete a uniquely
named index. Set `GREPVINE_SDK_TEST_ENDPOINT`, `GREPVINE_SDK_TEST_API_KEY`
and `GREPVINE_SDK_TEST_ORGANIZATION`, then run `uv run --frozen pytest`.

`scripts/check_package.py` installs the built wheel into a fresh environment
and runs synchronous and asynchronous requests against a mock transport, so a
packaging mistake fails CI. It also fails unless `LICENSE` is the verbatim
Apache License 2.0 text and the wheel and sdist declare `Apache-2.0` and
ship `LICENSE` and `NOTICE`. The distribution name is provisional until
registry availability is checked before release.

## Documentation

The documentation site is built with pdoc into the git-ignored `site/`
directory. Its landing page is `README.md`, followed by the reference grouped
by resource; `scripts/build_docs.py` lists the groups and fails when an
exported name is missing from them, when the README's sections are not the
guide's, when a page mentions the private `_generated` package, or when a page
uses a word the docs avoid. The build documents the resource classes and
models under `grepvine` and `grepvine.models`, folds the methods of each
resource's private base class into it, and adds to the `grepvine.models` page
a list of the models each resource uses, found from the method signatures. Any pdoc warning also fails the build. Open
`site/index.html` to read the result.

User-facing text (the README, docstrings and error messages) describes what
the SDK does, never how it is built: it does not say "generated", "raw",
"convenience", "wrapper" or "layer", and it follows Grepvine's rule that
internals never leak, so it never mentions how the service stores or indexes
data.

The theme lives in `docs/theme` and follows the Grepvine design system in
[`grepvine-ai/grepvine-design-system`](https://github.com/grepvine-ai/grepvine-design-system).
See `docs/theme/README.md` before changing it.

## Repository automation

The `Regenerate and validate SDK` workflow can be triggered manually. It
regenerates from the snapshot, runs tests and builds an installed-package
smoke test, then commits generated changes after the checks pass. Pushes and
pull requests validate reproducibility without committing. Grepvine's manual
`Update SDK snapshots` workflow updates both repositories and requests
regeneration.

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
GitHub release (not a pre-release), or running the workflow manually, also
deploys the site to GitHub Pages at the repository's default project URL. The
site documents the latest release only. Before the first deployment, set
**Settings → Pages → Source** to **GitHub Actions**; the workflow creates the
`github-pages` environment on its first run. The published site is public even
when the repository is private, and Pages on a private repository requires a
paid GitHub plan.
