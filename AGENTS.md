# Agent notes

- Generated code under `src/grepvine_sdk/_generated` is never edited by hand;
  change the generator configuration or adapter and regenerate. It is private:
  only `src/grepvine_sdk/_core/ops.py` imports its operations, and nothing
  public exposes it.
- The public interface follows the `grepvine` SDK in `grepvine-ai/grepvine`
  (`clients/python`) and the unified SDK design in that repository's
  `docs/specs/2026-10-15-unified-sdk-design.md`. Keep resource and method names
  identical to `grepvine-ai/grepvine-typescript-sdk`, apart from snake_case vs
  camelCase.
- Every API operation needs exactly one method on `Client` and on
  `AsyncClient`; `tests/test_coverage.py` enforces it. Add new operations to
  `_core/ops.py` and to both `_sync/resources.py` and `_async/resources.py`.
- User-facing text (README, docstrings, error messages) never says
  "generated", "raw", "convenience", "wrapper" or "layer", and never mentions
  how the service stores or indexes data. Contributor material belongs in
  `CONTRIBUTING.md`.
- The documentation site's theme follows the Grepvine design system in
  [`grepvine-ai/grepvine-design-system`](https://github.com/grepvine-ai/grepvine-design-system).
  Before changing anything under `docs/theme`, read `docs/theme/README.md` and
  the design system's `README.md`.
