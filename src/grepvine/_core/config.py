"""Endpoint and API key resolution.

The client uses the endpoint and API key it is given, and the default
endpoint when none is given. It reads no environment variables or files.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final
from urllib.parse import urlsplit

from grepvine.errors import ConfigurationError

DEFAULT_ENDPOINT: Final = "https://api.grepvine.ai"
API_VERSION_SUFFIX: Final = "/v1"

NOT_LOGGED_IN_MESSAGE: Final = (
    "no API key; pass api_key to the client or call configure(api_key=...)"
)


@dataclass(frozen=True, slots=True)
class Credentials:
    """Where requests go and how they authenticate."""

    endpoint: str
    api_key: str | None


def normalize_endpoint(raw: str) -> str:
    """Trim trailing slashes and make sure the endpoint ends in ``/v1``."""
    endpoint = raw.strip().rstrip("/")
    parts = urlsplit(endpoint)
    if parts.scheme not in {"http", "https"} or not parts.netloc:
        raise ConfigurationError(
            f"endpoint {raw!r} must be an http or https URL such as {DEFAULT_ENDPOINT}"
        )
    if parts.query or parts.fragment:
        raise ConfigurationError(f"endpoint {raw!r} must not carry a query or fragment")
    if endpoint.endswith(API_VERSION_SUFFIX):
        return endpoint
    return endpoint + API_VERSION_SUFFIX


def resolve_credentials(*, endpoint: str | None = None, api_key: str | None = None) -> Credentials:
    """Normalize the given endpoint, or use the default one, and keep the API key."""
    return Credentials(
        endpoint=normalize_endpoint(endpoint or DEFAULT_ENDPOINT),
        api_key=api_key or None,
    )
