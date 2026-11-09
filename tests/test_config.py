"""Client settings come from arguments, the environment and gv's configuration file."""

from __future__ import annotations

from pathlib import Path

import httpx
import pytest

import grepvine
from tests.conftest import Service, page_json


def write(path: Path, text: str, mode: int = 0o600) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    path.chmod(mode)
    return path


@pytest.fixture
def config_file(tmp_path: Path) -> Path:
    return write(
        tmp_path / ".grepvine/config.yaml",
        "endpoint: https://file.example\napi_key: gvk_file\norganization: acme\n",
    )


def sent(service: Service, client: grepvine.Client, name: str = "docs") -> tuple[str, str | None]:
    service.reply(httpx.Response(200, json=page_json([])))
    with client:
        list(client.index(name).search(pattern="x"))
    request = service.requests[-1]
    return str(request.url).split("?")[0], request.headers.get("Authorization")


def transport(service: Service) -> httpx.MockTransport:
    return httpx.MockTransport(service.handle)


def test_defaults_without_configuration(service: Service) -> None:
    client = grepvine.Client(transport=transport(service))
    assert client.settings == grepvine.Settings("https://api.grepvine.ai", None, None)


def test_configuration_file(service: Service, config_file: Path) -> None:
    client = grepvine.Client(transport=transport(service))
    assert sent(service, client) == (
        "https://file.example/v1/organizations/acme/indexes/docs/query",
        "Bearer gvk_file",
    )


def test_environment_overrides_the_file_per_setting(
    service: Service, config_file: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("GREPVINE_API_KEY", "gvk_env")
    client = grepvine.Client(transport=transport(service))
    assert sent(service, client) == (
        "https://file.example/v1/organizations/acme/indexes/docs/query",
        "Bearer gvk_env",
    )


def test_arguments_override_the_environment(
    service: Service, config_file: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("GREPVINE_API_KEY", "gvk_env")
    monkeypatch.setenv("GREPVINE_ORGANIZATION", "env-org")
    client = grepvine.Client(
        api_key="gvk_arg", organization="arg-org", transport=transport(service)
    )
    assert sent(service, client) == (
        "https://file.example/v1/organizations/arg-org/indexes/docs/query",
        "Bearer gvk_arg",
    )


def test_clients_configured_differently_side_by_side(
    service: Service, config_file: Path, tmp_path: Path
) -> None:
    staging = write(
        tmp_path / "staging.yaml",
        "endpoint: https://staging.example\napi_key: gvk_stage\norganization: beta\n",
    )
    default = grepvine.Client(transport=transport(service))
    other = grepvine.Client(config_file=staging, transport=transport(service))
    assert sent(service, default)[0].startswith("https://file.example/v1/organizations/acme/")
    assert sent(service, other) == (
        "https://staging.example/v1/organizations/beta/indexes/docs/query",
        "Bearer gvk_stage",
    )


def test_config_environment_variable_names_the_file(
    service: Service, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    other = write(tmp_path / "other.yaml", "organization: other\n")
    monkeypatch.setenv("GREPVINE_CONFIG", str(other))
    assert grepvine.Client(transport=transport(service)).settings.organization == "other"


def test_isolated_client_ignores_environment_and_file(
    service: Service, config_file: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("GREPVINE_API_KEY", "gvk_env")
    client = grepvine.Client(use_environment=False, transport=transport(service))
    assert client.settings == grepvine.Settings("https://api.grepvine.ai", None, None)


def test_index_without_organization_needs_one() -> None:
    with pytest.raises(grepvine.ConfigurationError, match="organization/docs"):
        grepvine.Client().index("docs")


def test_a_file_others_can_read_is_refused(config_file: Path) -> None:
    config_file.chmod(0o644)
    with pytest.raises(grepvine.ConfigurationError, match="chmod 600"):
        grepvine.Client()


def test_a_named_file_must_exist(tmp_path: Path) -> None:
    with pytest.raises(grepvine.ConfigurationError, match="does not exist"):
        grepvine.Client(config_file=tmp_path / "missing.yaml")


def test_a_file_must_be_a_mapping(tmp_path: Path) -> None:
    with pytest.raises(grepvine.ConfigurationError, match="must map"):
        grepvine.Client(config_file=write(tmp_path / "list.yaml", "- a\n"))


def test_module_level_index_uses_the_default_client(service: Service, config_file: Path) -> None:
    assert grepvine.default_client() is grepvine.default_client()
    grepvine.set_default_client(grepvine.Client(api_key="gvk_mine", transport=transport(service)))
    service.reply(httpx.Response(200, json=page_json([])))
    assert list(grepvine.index("docs").search(pattern="x")) == []
    request = service.requests[0]
    assert request.url.host == "file.example"
    assert request.headers["Authorization"] == "Bearer gvk_mine"
