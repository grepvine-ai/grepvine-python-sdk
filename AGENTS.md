# Agent notes

- Most of the package is generated. Generated code under
  `src/grepvine/_generated` is never edited by hand; change the contract
  snapshot, `sdk-operations.json`, `openapi-python-client.yaml`, the template
  in `scripts/templates` or the adapter in `scripts/generate.py`, and
  regenerate. It is private: nothing public mentions `_generated`, and the
  docs build fails when a page does.
- `sdk-operations.json` names every method and is identical in
  `grepvine-ai/grepvine-typescript-sdk`; change both together. Python names
  are the snake_case form of each segment.
- Hand-written code is limited to `_client.py`, `errors.py`, `_retry.py`,
  `_helpers.py` and `models.py`. Do not add methods that re-wrap a single
  operation; a new operation gets its method from the generator once the map
  has an entry. Keep helper names aligned with TypeScript: `paginate`,
  `wait_until_ready` / `waitUntilReady`, `authorize`, `put_many` / `putMany`.
- User-facing text (README, docstrings, error messages) never says
  "generated", "raw", "convenience", "wrapper" or "layer", and never mentions
  service internals such as storage, caches or background maintenance. Contributor material belongs in
  `CONTRIBUTING.md`.
- Before changing anything under `docs/theme`, read `docs/theme/README.md`.
