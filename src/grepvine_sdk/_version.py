"""The installed package version."""

from importlib import metadata

try:
    __version__ = metadata.version("grepvine-sdk")
except metadata.PackageNotFoundError:  # pragma: no cover - only when not installed
    __version__ = "0.0.0+unknown"
