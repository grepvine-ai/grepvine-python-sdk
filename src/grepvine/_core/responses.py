"""Checks on the decoded responses of API operations."""

from __future__ import annotations

from typing import Any, TypeVar

from grepvine.errors import GrepvineError

T = TypeVar("T")


def parsed(response: Any, model: type[T]) -> T:
    """The decoded body of a successful response, which must be a ``model``."""
    value = response.parsed
    if not isinstance(value, model):
        raise GrepvineError(
            f"the service returned an unexpected response (HTTP {int(response.status_code)})"
        )
    return value
