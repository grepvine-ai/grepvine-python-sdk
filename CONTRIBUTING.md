# Contributing to the Grepvine Python SDK

`README.md` is the user guide and the landing page of the documentation site.
This file covers how the SDK is built, tested, documented and released.

## How the SDK is built

The client is built on code generated from the API contract:

- `spec/openapi.json` is the full public contract, exported from
  `grepvine-ai/grepvine` without filtering operations or components.
  `spec/source.json` records the source repository, commit, the exported
  operation list, and the snapshot checksum. Change the contract in Grepvine,
  never the snapshot here.
- `scripts/generate.py` runs `openapi-python-client==0.29.1` (HTTPX and attrs
  models) on the snapshot and writes the private package
  `src/grepvine_sdk/_generated`: the transport, request and response models,
  and one module per operation with `sync_detailed` and `asyncio_detailed`
  functions. Never edit it by hand; change the contract, the generator
  configuration (`openapi-python-client.yaml`) or the adapter in
  `scripts/generate.py`, and regenerate.
- The adapter makes two equivalent changes before generating: the
  `If-None-Match` constant becomes a singleton enum, and the NDJSON batch body
  becomes a binary `File` whose bytes the template buffers so both HTTPX
  clients can send it. The original media type is kept. Generation fails on
  generator warnings or a missing operation.

The hand-written code adds only what a generator cannot know, following the
`grepvine` SDK's interface:

| Path | Contents |
| --- | --- |
| `src/grepvine_sdk/_core/ops.py` | Every operation, written once as a generator of effects. The only module that calls `_generated.api`. |
| `src/grepvine_sdk/_core/effects.py` | The effects an operation yields: call an API operation, sleep, read the clock, notify, set the session. |
| `src/grepvine_sdk/_core/config.py` | Endpoint and API key lookup, as `gv` does it. |
| `src/grepvine_sdk/_core/retry.py` | `RetryPolicy` and the retry decisions. |
| `src/grepvine_sdk/_core/paging.py`, `batching.py`, `metadata.py`, `build.py`, `parse.py` | Pagination, batch planning, metadata tagging, request validation, and reading documents. |
| `src/grepvine_sdk/_http.py` | Client state, the retrying HTTPX transports, and the hook that turns error responses into exceptions. |
| `src/grepvine_sdk/_sync`, `src/grepvine_sdk/_async` | `Client` and `AsyncClient`, their resources and paginators. Each interprets the effects of `ops.py`. |
| `src/grepvine_sdk/errors.py`, `models.py` | The public exceptions and result models. |

Every API request goes through a generated operation; the only HTTP the SDK
writes itself is the NDJSON batch body above. Retries live in the HTTPX
transport, so a retried request is the same request, idempotency key included.
`client.http` shares that transport.

`tests/test_coverage.py` checks that every operation listed in
`spec/source.json` is called by exactly one function in `ops.py`, and that
exactly one public method of each client uses it. When the API gains an
operation, CI fails until it has a method on both clients.

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

The tests run against an in-memory Grepvine service (`tests/fake_server.py`
and `tests/fake_accounts.py`) mounted with `httpx.MockTransport`, so they need
no network. Most tests run once with `Client` and once with `AsyncClient`
through the `fx` fixture. Warnings are errors.

Optional live tests in `tests/test_live.py` create and delete a uniquely
named index. Set `GREPVINE_SDK_TEST_ENDPOINT`, `GREPVINE_SDK_TEST_API_KEY`
and `GREPVINE_SDK_TEST_ORGANIZATION`, then run `uv run --frozen pytest`.

`scripts/check_package.py` installs the built wheel into a fresh environment
and runs synchronous and asynchronous requests against a mock transport, so a
packaging mistake fails CI. The distribution name is provisional until
registry availability is checked before release.

## Documentation

The documentation site is built with pdoc into the git-ignored `site/`
directory. Its landing page is `README.md`, followed by the reference grouped
by resource; `scripts/build_docs.py` lists the groups and fails when an
exported name is missing from them, when the README's sections are not the
guide's, when a page mentions the private `_generated` package, or when a page
uses a word the docs avoid. Any pdoc warning also fails the build. Open
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
