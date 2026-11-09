"""Client settings, resolved as gv resolves them: argument, environment, configuration file."""

from __future__ import annotations

import os
import stat
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import yaml

from grepvine.errors import ConfigurationError

DEFAULT_ENDPOINT: Final = "https://api.grepvine.ai"
DEFAULT_CONFIG_FILE: Final = "~/.grepvine/config.yaml"
ENVIRONMENT: Final = {
    "endpoint": "GREPVINE_API_ENDPOINT",
    "api_key": "GREPVINE_API_KEY",
    "organization": "GREPVINE_ORGANIZATION",
}


@dataclass(frozen=True)
class Settings:
    """The settings a client uses."""

    endpoint: str
    api_key: str | None
    organization: str | None


def environment() -> dict[str, str]:
    """The settings that ``GREPVINE_API_KEY``, ``GREPVINE_API_ENDPOINT`` and
    ``GREPVINE_ORGANIZATION`` give."""
    return {
        name: value for name, variable in ENVIRONMENT.items() if (value := os.environ.get(variable))
    }


def read_file(path: str | os.PathLike[str]) -> dict[str, str]:
    """The settings in a configuration file as ``gv`` writes it; other entries are ignored."""
    chosen = Path(path).expanduser()
    if not chosen.is_file():
        raise ConfigurationError(f"the configuration file {str(chosen)!r} does not exist")
    if os.name == "posix" and chosen.stat().st_mode & (stat.S_IRWXG | stat.S_IRWXO):
        raise ConfigurationError(f"other users can read {str(chosen)!r}; run chmod 600 on it")
    try:
        data = yaml.safe_load(chosen.read_text()) or {}
    except yaml.YAMLError as exc:
        raise ConfigurationError(f"{str(chosen)!r} is not valid YAML: {exc}") from exc
    if not isinstance(data, dict):
        raise ConfigurationError(f"{str(chosen)!r} must map setting names to values")
    return {name: str(data[name]) for name in ENVIRONMENT if data.get(name) not in (None, "")}


def default_file() -> dict[str, str]:
    """The settings in ``$GREPVINE_CONFIG``, else in ``~/.grepvine/config.yaml`` when it exists."""
    if named := os.environ.get("GREPVINE_CONFIG"):
        return read_file(named)
    path = Path(DEFAULT_CONFIG_FILE).expanduser()
    return read_file(path) if path.exists() else {}


def resolve(
    *,
    endpoint: str | None = None,
    api_key: str | None = None,
    organization: str | None = None,
    trust_env: bool,
) -> Settings:
    """Each setting from its argument, else, with ``trust_env``, its environment variable, else
    the configuration file, else its default."""
    layers: list[Mapping[str, str | None]] = [
        {"endpoint": endpoint, "api_key": api_key, "organization": organization}
    ]
    if trust_env:
        layers += [environment(), default_file()]
    values = {
        name: next((layer[name] for layer in layers if layer.get(name)), None)
        for name in ENVIRONMENT
    }
    return Settings(
        endpoint=values["endpoint"] or DEFAULT_ENDPOINT,
        api_key=values["api_key"],
        organization=values["organization"],
    )
