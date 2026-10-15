from __future__ import annotations

import httpx
import pytest

from grepvine import Client, ConfigurationError
from grepvine._core.config import DEFAULT_ENDPOINT, normalize_endpoint, resolve_credentials


def test_explicit_endpoint_and_key() -> None:
    resolved = resolve_credentials(endpoint="http://explicit:9", api_key="gvk_explicit")
    assert (resolved.endpoint, resolved.api_key) == ("http://explicit:9/v1", "gvk_explicit")


def test_defaults_without_arguments() -> None:
    resolved = resolve_credentials()
    assert (resolved.endpoint, resolved.api_key) == (DEFAULT_ENDPOINT + "/v1", None)
    resolved = resolve_credentials(endpoint="", api_key="")
    assert (resolved.endpoint, resolved.api_key) == (DEFAULT_ENDPOINT + "/v1", None)


def test_environment_is_not_read(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GREPVINE_API_KEY", "gvk_env")
    monkeypatch.setenv("GREPVINE_API_ENDPOINT", "http://env:1")
    monkeypatch.setenv("GREPVINE_ENDPOINT", "http://alias:2")
    config = Client().config
    assert (config.endpoint, config.api_key) == (DEFAULT_ENDPOINT + "/v1", None)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("https://api.grepvine.ai", "https://api.grepvine.ai/v1"),
        ("https://api.grepvine.ai/", "https://api.grepvine.ai/v1"),
        ("https://api.grepvine.ai/v1", "https://api.grepvine.ai/v1"),
        ("https://api.grepvine.ai/v1/", "https://api.grepvine.ai/v1"),
        ("http://localhost:8080///", "http://localhost:8080/v1"),
        (" http://h:1 ", "http://h:1/v1"),
    ],
)
def test_normalize_endpoint(raw: str, expected: str) -> None:
    assert normalize_endpoint(raw) == expected


@pytest.mark.parametrize(
    "raw",
    [
        "localhost:8080",
        "api.grepvine.ai",
        "ftp://x",
        "http://",
        "http://h?x=1",
        "http://h#frag",
        "",
    ],
)
def test_normalize_endpoint_rejects_unusable_urls(raw: str) -> None:
    with pytest.raises(ConfigurationError):
        normalize_endpoint(raw)


def test_client_config_fields() -> None:
    client = Client(api_key="gvk_x", endpoint="http://h", timeout=5)
    config = client.config
    assert config.timeout == httpx.Timeout(5)
    assert config.user_agent.startswith("grepvine-python-sdk/")
    assert "python-httpx/" in config.user_agent
    assert client.config is config
    custom = httpx.Timeout(1.0, read=9.0)
    assert Client(timeout=custom, api_key="k", endpoint="http://h").config.timeout is custom
