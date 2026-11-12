"""Exceptions raised by the Grepvine SDK."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import Any

import httpx

from grepvine.models import MutationResult

__all__ = [
    "APIError",
    "AuthenticationError",
    "ConfigurationError",
    "ConflictError",
    "GrepvineError",
    "InvalidPageError",
    "InvalidRequestError",
    "NotFoundError",
    "OperationFailedError",
    "PartialBatchError",
    "PayloadTooLargeError",
    "PermissionDeniedError",
    "PreconditionFailedError",
    "RangeNotSatisfiableError",
    "RateLimitedError",
    "ServerError",
    "TransportError",
    "WaitError",
    "WaitTimeoutError",
]


class GrepvineError(Exception):
    """Base class of every error raised by the SDK."""


class ConfigurationError(GrepvineError):
    """The client cannot be used as configured, for example with an endpoint that is not a URL."""


class WaitError(GrepvineError):
    """Waiting for work the service finishes in the background ended before the work was done.

    ``target`` names what was waited for, such as ``"index acme/docs"``, and
    ``state`` is the last state seen. Catch ``WaitError`` for either way a wait
    can end without success: `WaitTimeoutError` or `OperationFailedError`.
    """

    def __init__(self, message: str, *, target: str, state: str | None) -> None:
        super().__init__(message)
        self.target = target
        self.state = state


class WaitTimeoutError(WaitError, TimeoutError):
    """The work was not done within the wait's ``timeout``, in seconds.

    The work goes on in the service; wait again to keep waiting. It is also a
    built-in ``TimeoutError``.
    """

    def __init__(self, *, target: str, state: str | None, timeout: float) -> None:
        super().__init__(
            f"{target} was not done within {timeout:g}s; it is {state}", target=target, state=state
        )
        self.timeout = timeout


class OperationFailedError(WaitError):
    """The work reached a state it will not leave by itself, such as ``delete_failed``.

    Waiting longer does not help; contact support if it persists.
    """

    def __init__(self, *, target: str, state: str) -> None:
        super().__init__(f"{target} is {state}", target=target, state=state)


class TransportError(GrepvineError):
    """The request could not be delivered after the configured attempts."""

    def __init__(self, message: str, *, cause: BaseException | None = None) -> None:
        super().__init__(message)
        self.__cause__ = cause


class APIError(GrepvineError):
    """The service answered with an error.

    ``code`` says what went wrong in machine-readable form, ``message`` is the
    service's sentence about it, and ``request_id`` identifies the request for
    support. ``details`` holds structured information about the error, each a
    mapping with ``type`` and ``metadata``; ignore types you do not know. A
    ``"missing_permission"`` detail names in ``metadata["permission"]`` the
    permission the API key lacks.
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
        details: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.reason = reason
        self.message = message
        self.request_id = request_id
        self.retry_after = retry_after
        self.details = details or []

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
    including ``amount``, as the request that produced them.
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

    ``documents.put`` and ``documents.delete`` raise it. The batch methods
    report a failed condition in the document's result instead.
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
    """``documents.put_many`` failed after the service had answered some of its requests.

    ``committed`` holds the results of the documents the service answered for,
    in input order; a document it left unchanged carries an ``error`` there.
    ``failed_keys`` are the keys of the request that failed; the service may
    have applied some of them before the failure. ``pending_keys`` were never
    attempted. ``__cause__`` is the underlying error. When the call was given
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
        applied = sum(1 for result in committed if not result.error)
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


def map_error(response: httpx.Response) -> APIError:
    """Translate an error response into the matching :class:`APIError` subclass.

    Every error answer goes through this function. The response body must have been read.
    """
    try:
        body: Any = json.loads(response.content)
    except ValueError:
        body = None
    body = body if isinstance(body, Mapping) else {}
    status = response.status_code
    code = str(body.get("code") or "request_failed")
    cls = _BY_STATUS.get(status, ServerError if status >= 500 else APIError)
    retry_after = response.headers.get("retry-after", "").strip()
    return (InvalidPageError if code == "invalid_page" and status == 400 else cls)(
        status_code=status,
        code=code,
        reason=str(body.get("reason") or "http"),
        message=str(body.get("error") or f"HTTP {status}"),
        request_id=response.headers.get("x-request-id") or None,
        retry_after=int(retry_after) if retry_after.isdigit() else None,
        details=[dict(d) for d in body.get("details") or [] if isinstance(d, Mapping)],
    )
