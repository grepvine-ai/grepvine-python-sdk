"""Exceptions raised by the Grepvine SDK."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any

import httpx

if TYPE_CHECKING:
    from grepvine_sdk.models import MutationResult

__all__ = [
    "APIError",
    "AuthenticationError",
    "ConfigurationError",
    "ConflictError",
    "GrepvineError",
    "InvalidPageError",
    "InvalidRequestError",
    "NotFoundError",
    "PartialBatchError",
    "PayloadTooLargeError",
    "PermissionDeniedError",
    "PreconditionFailedError",
    "RangeNotSatisfiableError",
    "RateLimitedError",
    "ServerError",
    "TransportError",
]


class GrepvineError(Exception):
    """Base class of every error raised by the SDK."""


class ConfigurationError(GrepvineError):
    """The client is not configured: no API key, or an unusable endpoint or configuration file."""


class TransportError(GrepvineError):
    """The request could not be delivered after the configured attempts."""

    def __init__(self, message: str, *, cause: BaseException | None = None) -> None:
        super().__init__(message)
        self.__cause__ = cause


class APIError(GrepvineError):
    """The service answered with an error.

    ``code`` says what went wrong in machine-readable form, ``message`` is the
    service's sentence about it, and ``request_id`` identifies the request for
    support.
    """

    def __init__(
        self,
        *,
        status_code: int,
        code: str,
        reason: str,
        message: str,
        request_id: str | None = None,
        retry_after: int | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.reason = reason
        self.message = message
        self.request_id = request_id
        self.retry_after = retry_after

    def __str__(self) -> str:
        if self.request_id:
            return f"{self.message} ({self.code}; request {self.request_id})"
        return f"{self.message} ({self.code})"

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}(status_code={self.status_code}, code={self.code!r}, "
            f"message={self.message!r}, request_id={self.request_id!r})"
        )


class InvalidRequestError(APIError):
    """The request was rejected (HTTP 400). Fix the input and try again."""


class InvalidPageError(InvalidRequestError):
    """The page token is invalid.

    Tokens expire after 15 minutes and are valid only with the same arguments,
    including ``page_size``, as the request that produced them.
    """


class AuthenticationError(APIError):
    """The API key is missing or not valid (HTTP 401)."""


class PermissionDeniedError(APIError):
    """The API key may not perform this action (HTTP 403)."""


class NotFoundError(APIError):
    """The resource does not exist or is not visible to this API key (HTTP 404)."""


class ConflictError(APIError):
    """The request conflicts with the current state (HTTP 409)."""


class PreconditionFailedError(APIError):
    """An ``if_match`` or ``if_none_match`` condition did not hold (HTTP 412).

    Only the single-document forms raise it. The list forms report a failed
    condition in the document's :attr:`~grepvine_sdk.MutationResult.error`.
    """


class PayloadTooLargeError(APIError):
    """The document or batch exceeds a size limit (HTTP 413)."""


class RangeNotSatisfiableError(APIError):
    """The requested byte range does not overlap the document (HTTP 416)."""


class RateLimitedError(APIError):
    """The service asked the client to slow down for longer than the client was willing to wait."""


class ServerError(APIError):
    """The service failed (HTTP 5xx) on every attempt."""


class PartialBatchError(GrepvineError):
    """A list-form write failed after the service had answered some of its requests.

    ``committed`` holds the results of the documents the service answered for,
    in input order; a document it left unchanged carries an ``error`` there.
    ``failed_keys`` are the keys of the request that failed; the service may
    have applied some of them before the failure. ``pending_keys`` were never
    attempted. ``__cause__`` is the underlying error. When the write was given
    an ``idempotency_key``, repeating it with the same key and the same
    documents finishes it without applying any document twice.
    """

    def __init__(
        self,
        *,
        committed: Sequence[MutationResult],
        failed_keys: Sequence[str],
        pending_keys: Sequence[str],
        cause: GrepvineError,
    ) -> None:
        applied = sum(1 for result in committed if result.ok)
        unchanged = len(committed) - applied
        left = f", {unchanged} were left unchanged," if unchanged else ""
        super().__init__(
            f"{len(failed_keys)} document(s) failed after {applied} were written{left} "
            f"and {len(pending_keys)} were not attempted: {cause}"
        )
        self.committed: tuple[MutationResult, ...] = tuple(committed)
        self.failed_keys: tuple[str, ...] = tuple(failed_keys)
        self.pending_keys: tuple[str, ...] = tuple(pending_keys)
        self.__cause__ = cause


_BY_STATUS: dict[int, type[APIError]] = {
    400: InvalidRequestError,
    401: AuthenticationError,
    403: PermissionDeniedError,
    404: NotFoundError,
    409: ConflictError,
    412: PreconditionFailedError,
    413: PayloadTooLargeError,
    416: RangeNotSatisfiableError,
    429: RateLimitedError,
}


def parse_retry_after(headers: Mapping[str, str]) -> int | None:
    """Return the ``Retry-After`` header as whole seconds, or None when absent or unusable."""
    value = headers.get("retry-after", "").strip()
    if not value.isdigit():
        return None
    return int(value)


def _error_body(response: httpx.Response) -> tuple[str, str, str]:
    try:
        body: Any = json.loads(response.content)
    except ValueError:
        body = None
    if not isinstance(body, Mapping):
        return "request_failed", "http", f"HTTP {response.status_code}"
    code = body.get("code")
    reason = body.get("reason")
    message = body.get("error")
    return (
        str(code) if code else "request_failed",
        str(reason) if reason else "http",
        str(message) if message else f"HTTP {response.status_code}",
    )


def map_error(response: httpx.Response, *, message_suffix: str = "") -> APIError:
    """Translate an error response into the matching :class:`APIError` subclass.

    The response body must have been read.
    """
    status = response.status_code
    code, reason, message = _error_body(response)
    cls: type[APIError]
    if status == 400 and code == "invalid_page":
        cls = InvalidPageError
    elif status in _BY_STATUS:
        cls = _BY_STATUS[status]
    elif status >= 500:
        cls = ServerError
    else:
        cls = APIError
    return cls(
        status_code=status,
        code=code,
        reason=reason,
        message=message + message_suffix,
        request_id=response.headers.get("x-request-id") or None,
        retry_after=parse_retry_after(response.headers),
    )
