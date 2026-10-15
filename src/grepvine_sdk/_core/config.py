"""Endpoint and API key resolution, identical to the ``gv`` command-line client.

The endpoint comes from ``GREPVINE_API_ENDPOINT``, then ``GREPVINE_ENDPOINT``,
then the ``endpoint`` key of ``~/.grepvine/config.yaml``, then the default.
The API key comes from ``GREPVINE_API_KEY``, then the ``api_key`` key of the
same file. An explicit argument wins over all of them. The SDK reads the file
``gv login`` writes and never writes it.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Final
from urllib.parse import urlsplit

import yaml

from grepvine_sdk.errors import ConfigurationError

DEFAULT_ENDPOINT: Final = "https://api.grepvine.ai"
API_VERSION_SUFFIX: Final = "/v1"
ENV_ENDPOINT: Final = "GREPVINE_API_ENDPOINT"
ENV_ENDPOINT_ALIAS: Final = "GREPVINE_ENDPOINT"
ENV_API_KEY: Final = "GREPVINE_API_KEY"
CONFIG_FILE_KEYS: Final = frozenset({"endpoint", "api_key"})

NOT_LOGGED_IN_MESSAGE: Final = (
    "not logged in; run `gv login`, set GREPVINE_API_KEY, or pass api_key to the client"
)


@dataclass(frozen=True, slots=True)
class FileConfig:
    """The two optional keys of ``~/.grepvine/config.yaml``."""

    endpoint: str | None = None
    api_key: str | None = None


@dataclass(frozen=True, slots=True)
class Credentials:
    """Where requests go and how they authenticate."""

    endpoint: str
    api_key: str | None
    config_path: Path


def default_config_path() -> Path:
    return Path.home() / ".grepvine" / "config.yaml"


def load_config_file(path: Path) -> FileConfig:
    """Read the configuration file; a missing file is an empty configuration."""
    try:
        data = path.read_bytes()
    except FileNotFoundError:
        return FileConfig()
    except OSError as exc:
        raise ConfigurationError(f"read configuration {path}: {exc.strerror or exc}") from exc
    if os.name != "nt":
        mode = path.stat().st_mode & 0o777
        if mode & 0o077:
            raise ConfigurationError(f"configuration {path} must have mode 0600")
    try:
        loaded = yaml.safe_load(data)
    except yaml.YAMLError as exc:
        raise ConfigurationError(f"parse configuration {path}: {exc}") from exc
    if loaded is None:
        return FileConfig()
    if not isinstance(loaded, Mapping):
        raise ConfigurationError(f"parse configuration {path}: expected a mapping")
    unknown = sorted(str(key) for key in loaded if key not in CONFIG_FILE_KEYS)
    if unknown:
        raise ConfigurationError(f"parse configuration {path}: unknown key(s) {', '.join(unknown)}")
    values: dict[str, str | None] = {}
    for key in CONFIG_FILE_KEYS:
        value = loaded.get(key)
        if value is not None and not isinstance(value, str):
            raise ConfigurationError(f"parse configuration {path}: {key} must be a string")
        values[key] = value
    return FileConfig(endpoint=values["endpoint"], api_key=values["api_key"])


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


def _present(value: str | None) -> str | None:
    return value if value else None


def resolve_credentials(
    *,
    endpoint: str | None = None,
    api_key: str | None = None,
    env: Mapping[str, str],
    config_path: Path | None = None,
) -> Credentials:
    """Resolve the endpoint and API key through the ``gv`` chain.

    The configuration file is read only when a value is still missing after
    the explicit arguments and the environment.
    """
    path = config_path or default_config_path()
    file_config: FileConfig | None = None

    def from_file(key: str) -> str | None:
        nonlocal file_config
        if file_config is None:
            file_config = load_config_file(path)
        return _present(getattr(file_config, key))

    resolved_endpoint = (
        _present(endpoint)
        or _present(env.get(ENV_ENDPOINT))
        or _present(env.get(ENV_ENDPOINT_ALIAS))
        or from_file("endpoint")
        or DEFAULT_ENDPOINT
    )
    resolved_key = _present(api_key) or _present(env.get(ENV_API_KEY)) or from_file("api_key")
    return Credentials(
        endpoint=normalize_endpoint(resolved_endpoint),
        api_key=resolved_key,
        config_path=path,
    )
