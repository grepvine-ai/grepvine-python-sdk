from __future__ import annotations

import os
from pathlib import Path

import httpx
import pytest

from grepvine import Client, ConfigurationError
from grepvine._core.config import (
    DEFAULT_ENDPOINT,
    FileConfig,
    default_config_path,
    load_config_file,
    normalize_endpoint,
    resolve_credentials,
)


@pytest.fixture
def config_file(tmp_path: Path) -> Path:
    path = tmp_path / "config.yaml"
    path.write_text("endpoint: http://file:8080\napi_key: gvk_file\n")
    path.chmod(0o600)
    return path


def test_precedence_explicit_env_alias_file_default(config_file: Path) -> None:
    env = {
        "GREPVINE_API_ENDPOINT": "http://env:1/",
        "GREPVINE_ENDPOINT": "http://alias:2",
        "GREPVINE_API_KEY": "gvk_env",
    }
    resolved = resolve_credentials(
        endpoint="http://explicit:9", api_key="gvk_explicit", env=env, config_path=config_file
    )
    assert (resolved.endpoint, resolved.api_key) == ("http://explicit:9/v1", "gvk_explicit")

    resolved = resolve_credentials(env=env, config_path=config_file)
    assert (resolved.endpoint, resolved.api_key) == ("http://env:1/v1", "gvk_env")

    del env["GREPVINE_API_ENDPOINT"]
    resolved = resolve_credentials(env=env, config_path=config_file)
    assert resolved.endpoint == "http://alias:2/v1"

    del env["GREPVINE_ENDPOINT"]
    del env["GREPVINE_API_KEY"]
    resolved = resolve_credentials(env=env, config_path=config_file)
    assert (resolved.endpoint, resolved.api_key) == ("http://file:8080/v1", "gvk_file")
    assert resolved.config_path == config_file

    resolved = resolve_credentials(env={}, config_path=config_file.with_name("missing.yaml"))
    assert (resolved.endpoint, resolved.api_key) == (f"{DEFAULT_ENDPOINT}/v1", None)


def test_empty_values_count_as_unset(config_file: Path) -> None:
    env = {"GREPVINE_API_ENDPOINT": "", "GREPVINE_ENDPOINT": "", "GREPVINE_API_KEY": ""}
    resolved = resolve_credentials(endpoint="", api_key="", env=env, config_path=config_file)
    assert (resolved.endpoint, resolved.api_key) == ("http://file:8080/v1", "gvk_file")


def test_endpoint_and_key_resolve_independently(config_file: Path) -> None:
    resolved = resolve_credentials(
        env={"GREPVINE_API_ENDPOINT": "http://env:1"}, config_path=config_file
    )
    assert (resolved.endpoint, resolved.api_key) == ("http://env:1/v1", "gvk_file")


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


def test_load_config_file_cases(tmp_path: Path) -> None:
    assert load_config_file(tmp_path / "missing.yaml") == FileConfig()

    empty = tmp_path / "empty.yaml"
    empty.write_text("")
    empty.chmod(0o600)
    assert load_config_file(empty) == FileConfig()

    only_key = tmp_path / "key.yaml"
    only_key.write_text("api_key: gvk_x\n")
    only_key.chmod(0o600)
    assert load_config_file(only_key) == FileConfig(api_key="gvk_x")

    directory = tmp_path / "dir"
    directory.mkdir()
    with pytest.raises(ConfigurationError, match="read configuration"):
        load_config_file(directory)

    for content, message in [
        ("- a\n- b\n", "expected a mapping"),
        ("endpoint: http://x\nprofile: dev\n", "unknown key"),
        ("api_key: [1, 2]\n", "must be a string"),
        ("not: [valid", "parse configuration"),
    ]:
        bad = tmp_path / "bad.yaml"
        bad.write_text(content)
        bad.chmod(0o600)
        with pytest.raises(ConfigurationError, match=message):
            load_config_file(bad)


def test_permission_check(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / "config.yaml"
    path.write_text("api_key: gvk_x\n")
    path.chmod(0o644)
    with pytest.raises(ConfigurationError, match="must have mode 0600"):
        load_config_file(path)
    path.chmod(0o640)
    with pytest.raises(ConfigurationError, match="must have mode 0600"):
        load_config_file(path)
    path.chmod(0o400)
    assert load_config_file(path) == FileConfig(api_key="gvk_x")

    path.chmod(0o644)
    monkeypatch.setattr(os, "name", "nt")
    assert load_config_file(path) == FileConfig(api_key="gvk_x")


def test_default_config_path() -> None:
    assert default_config_path() == Path.home() / ".grepvine" / "config.yaml"


def test_explicit_arguments_never_read_the_file(tmp_path: Path) -> None:
    path = tmp_path / "config.yaml"
    path.write_text("api_key: gvk_x\n")
    path.chmod(0o644)
    client = Client(api_key="gvk_explicit", endpoint="http://h", env={}, config_path=path)
    assert client.config.api_key == "gvk_explicit"

    lazy = Client(endpoint="http://h", env={}, config_path=path)
    with pytest.raises(ConfigurationError, match="mode 0600"):
        lazy.config  # noqa: B018 - resolving is the point


def test_client_config_fields(tmp_path: Path) -> None:
    client = Client(
        api_key="gvk_x", endpoint="http://h", env={}, config_path=tmp_path / "c", timeout=5
    )
    config = client.config
    assert config.timeout == httpx.Timeout(5)
    assert config.user_agent.startswith("grepvine-python-sdk/")
    assert "python-httpx/" in config.user_agent
    assert client.config is config
    custom = httpx.Timeout(1.0, read=9.0)
    assert Client(timeout=custom, api_key="k", endpoint="http://h", env={}).config.timeout is custom
