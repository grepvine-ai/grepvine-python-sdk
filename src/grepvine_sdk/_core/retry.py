"""Retry and slow-down decisions, ported from the ``gv`` command-line client.

A 429 answer pauses every request of the client for the server's interval
(with jitter) and never consumes an attempt; a 5xx answer or a transport
failure is retried a fixed number of times with a short backoff; any other
answer is delivered to the operation.
"""

from __future__ import annotations

import random
from collections.abc import Mapping
from dataclasses import dataclass
from typing import TypeAlias

import httpx


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    """How a client retries failed requests.

    ``max_attempts`` bounds 5xx and transport retries; ``backoff`` gives the
    sleep after each failed attempt (the last value repeats). A 429 pauses the
    client for ``Retry-After`` seconds (``default_retry_after`` when the header
    is missing, never more than ``max_retry_after``), with a random adjustment
    of up to ``retry_after_jitter`` in either direction, until one request has
    waited ``max_throttled_wait`` seconds in total.
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

    def backoff_for(self, attempt: int) -> float:
        """Seconds to sleep after the given one-based failed attempt."""
        if not self.backoff:
            return 0.0
        return self.backoff[min(attempt, len(self.backoff)) - 1]


@dataclass(frozen=True, slots=True)
class Deliver:
    """Hand the response to the operation.

    ``throttled_wait`` is set when the response is a 429 the client stopped
    waiting out, with the seconds it had already waited.
    """

    throttled_wait: float | None = None


@dataclass(frozen=True, slots=True)
class Fail:
    """Give up: the request could not be delivered."""


@dataclass(frozen=True, slots=True)
class PauseThen:
    seconds: float


@dataclass(frozen=True, slots=True)
class BackoffThen:
    seconds: float


Decision: TypeAlias = Deliver | Fail | PauseThen | BackoffThen


def retry_after_seconds(
    headers: Mapping[str, str], policy: RetryPolicy, rng: random.Random
) -> float:
    """The pause a 429 asks for, bounded and with jitter applied."""
    raw = headers.get("retry-after", "").strip()
    delay = policy.default_retry_after
    if raw.isdigit() and int(raw) > 0:
        delay = float(int(raw))
    delay = min(delay, policy.max_retry_after)
    jitter = rng.uniform(-1.0, 1.0) * policy.retry_after_jitter * delay
    return delay + jitter


def decide(
    outcome: httpx.Response | httpx.TransportError,
    *,
    attempt: int,
    throttled_wait: float,
    policy: RetryPolicy,
    rng: random.Random,
) -> Decision:
    """Decide what to do with the outcome of the given one-based attempt."""
    if isinstance(outcome, httpx.TransportError):
        if attempt >= policy.max_attempts:
            return Fail()
        return BackoffThen(policy.backoff_for(attempt))
    if outcome.status_code == 429:
        delay = retry_after_seconds(outcome.headers, policy, rng)
        if throttled_wait + delay > policy.max_throttled_wait:
            return Deliver(throttled_wait)
        return PauseThen(delay)
    if outcome.status_code >= 500 and attempt < policy.max_attempts:
        return BackoffThen(policy.backoff_for(attempt))
    return Deliver()
