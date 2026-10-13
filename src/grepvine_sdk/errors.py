"""Exceptions raised by the convenience API."""

from collections.abc import Mapping

from .generated.models import Error, MutationResult


class ApiError(Exception):
    """An API failure with its original status and support/retry details."""

    def __init__(self, status: int, error: Error | None, headers: Mapping[str, str]) -> None:
        self.status = status
        self.code = error.code if error else "invalid_response"
        self.reason = error.reason if error else "response"
        self.request_id = headers.get("X-Request-ID")
        self.headers = dict(headers)
        self.retry_after: int | None = None
        try:
            self.retry_after = max(0, int(headers["Retry-After"]))
        except (KeyError, ValueError):
            self.retry_after = None
        super().__init__(error.error if error else "The service returned an unexpected response.")


class BatchError(Exception):
    """Some documents failed. results retains successes as well as failures."""

    def __init__(self, results: list[MutationResult], request_id: str | None) -> None:
        self.results = results
        self.failures = [
            item for item in results if isinstance(item.error, Error) or not item.revision
        ]
        self.request_id = request_id
        super().__init__(f"{len(self.failures)} of {len(results)} documents were not stored.")
