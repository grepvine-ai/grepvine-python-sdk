"""Retries in the HTTPX transport, so a retried request is the same request."""

from __future__ import annotations

import asyncio
import random
import time
import uuid
from dataclasses import dataclass

import httpx

from grepvine.errors import TransportError

# Looked up on every call, so tests can replace them.
sleep = time.sleep
async_sleep = asyncio.sleep
monotonic = time.monotonic

_SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    """How a client retries failed requests.

    A 5xx answer or a failure to reach the service is retried until
    ``max_attempts`` attempts were made, sleeping ``backoff[n]`` seconds after
    the n-th failure (the last value repeats). A 429 answer waits
    ``Retry-After`` seconds (``default_retry_after`` when the header is
    missing, at most ``max_retry_after``), adjusted at random by up to
    ``retry_after_jitter`` of the delay either way, and does not count as an
    attempt; once a request has waited ``max_throttled_wait`` seconds in total,
    the 429 raises :class:`~grepvine.RateLimitedError`.
    """

    max_attempts: int = 3
    backoff: tuple[float, ...] = (0.1, 0.2)
    default_retry_after: float = 1.0
    max_retry_after: float = 60.0
    retry_after_jitter: float = 0.25
    max_throttled_wait: float = 600.0

    def __post_init__(self) -> None:
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")
        if not 0 <= self.retry_after_jitter < 1:
            raise ValueError("retry_after_jitter must be in [0, 1)")

    def _backoff(self, attempt: int) -> float:
        return self.backoff[min(attempt, len(self.backoff)) - 1] if self.backoff else 0.0

    def _retry_after(self, response: httpx.Response) -> float:
        header = response.headers.get("retry-after", "").strip()
        delay = float(header) if header.isdigit() and int(header) > 0 else self.default_retry_after
        delay = min(delay, self.max_retry_after)
        return delay * (1 + random.uniform(-1.0, 1.0) * self.retry_after_jitter)


class _Attempts:
    """The retry decisions for one request: how long to wait before the next attempt, or None."""

    def __init__(self, policy: RetryPolicy, request: httpx.Request) -> None:
        self.policy = policy
        self.attempt = 1
        self.throttled = 0.0
        # Every write carries an idempotency key, and every attempt carries the same one.
        if request.method not in _SAFE_METHODS and "idempotency-key" not in request.headers:
            request.headers["Idempotency-Key"] = uuid.uuid4().hex

    def after_failure(self, exc: httpx.TransportError) -> float:
        if self.attempt >= self.policy.max_attempts:
            raise TransportError(
                f"the request failed after {self.attempt} attempt(s): {exc}", cause=exc
            ) from exc
        self.attempt += 1
        return self.policy._backoff(self.attempt - 1)

    def after_response(self, response: httpx.Response) -> float | None:
        if response.status_code == 429:
            delay = self.policy._retry_after(response)
            if self.throttled + delay > self.policy.max_throttled_wait:
                return None
            self.throttled += delay
            return delay
        if response.status_code >= 500 and self.attempt < self.policy.max_attempts:
            self.attempt += 1
            return self.policy._backoff(self.attempt - 1)
        return None


class RetryTransport(httpx.BaseTransport):
    def __init__(self, inner: httpx.BaseTransport, policy: RetryPolicy) -> None:
        self._inner = inner
        self._policy = policy

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        attempts = _Attempts(self._policy, request)
        while True:
            try:
                response = self._inner.handle_request(request)
            except httpx.TransportError as exc:
                delay = attempts.after_failure(exc)
            else:
                if (delay_or_none := attempts.after_response(response)) is None:
                    return response
                delay = delay_or_none
                response.close()
            sleep(delay)

    def close(self) -> None:
        self._inner.close()


class AsyncRetryTransport(httpx.AsyncBaseTransport):
    def __init__(self, inner: httpx.AsyncBaseTransport, policy: RetryPolicy) -> None:
        self._inner = inner
        self._policy = policy

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        attempts = _Attempts(self._policy, request)
        while True:
            try:
                response = await self._inner.handle_async_request(request)
            except httpx.TransportError as exc:
                delay = attempts.after_failure(exc)
            else:
                if (delay_or_none := attempts.after_response(response)) is None:
                    return response
                delay = delay_or_none
                await response.aclose()
            await async_sleep(delay)

    async def aclose(self) -> None:
        await self._inner.aclose()
