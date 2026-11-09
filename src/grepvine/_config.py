"""Client settings, resolved as gv resolves them: argument, environment, configuration file."""

from __future__ import annotations

import os
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final

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


def _read(path: str | os.PathLike[str] | None) -> dict[str, Any]:
    named = path is not None or bool(os.environ.get("GREPVINE_CONFIG"))
    chosen = Path(path or os.environ.get("GREPVINE_CONFIG") or DEFAULT_CONFIG_FILE).expanduser()
    if not chosen.exists():
        if named:
            raise ConfigurationError(f"the configuration file {str(chosen)!r} does not exist")
        return {}
    if os.name == "posix" and chosen.stat().st_mode & (stat.S_IRWXG | stat.S_IRWXO):
        raise ConfigurationError(f"other users can read {str(chosen)!r}; run chmod 600 on it")
    try:
        data = yaml.safe_load(chosen.read_text()) or {}
    except yaml.YAMLError as exc:
        raise ConfigurationError(f"{str(chosen)!r} is not valid YAML: {exc}") from exc
    if not isinstance(data, dict):
        raise ConfigurationError(f"{str(chosen)!r} must map setting names to values")
    return data


def resolve(
    *,
    endpoint: str | None,
    api_key: str | None,
    organization: str | None,
    config_file: str | os.PathLike[str] | None,
    use_environment: bool,
) -> Settings:
    """Each setting from its argument, else its environment variable, else the file, else its
    default. With ``use_environment=False``, only the arguments and an explicit ``config_file``."""
    given = {"endpoint": endpoint, "api_key": api_key, "organization": organization}
    stored = _read(config_file) if use_environment or config_file is not None else {}
    values = {
        name: given[name]
        or (os.environ.get(variable) if use_environment else None)
        or stored.get(name)
        for name, variable in ENVIRONMENT.items()
    }
    return Settings(
        endpoint=str(values["endpoint"] or DEFAULT_ENDPOINT),
        api_key=values["api_key"] and str(values["api_key"]),
        organization=values["organization"] and str(values["organization"]),
    )
