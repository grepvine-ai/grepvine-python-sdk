from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import httpx
import pytest

import grepvine as grepvine
from grepvine import Client, ConfigurationError
from tests.fake_server import API_KEY, FakeGrepvine


def test_module_namespace_is_bound_to_the_default_client() -> None:
    assert isinstance(grepvine.default_client, Client)
    assert grepvine.organizations is grepvine.default_client.organizations
    assert grepvine.indexes is grepvine.default_client.indexes
    assert grepvine.configure == grepvine.default_client.configure
    assert grepvine.__version__


def test_import_does_not_read_configuration(tmp_path: Path) -> None:
    config = tmp_path / ".grepvine" / "config.yaml"
    config.parent.mkdir()
    config.write_text("not: [valid")
    config.chmod(0o644)
    env = {
        **os.environ,
        "HOME": str(tmp_path),
        "USERPROFILE": str(tmp_path),
        "PYTHONPATH": str(Path(grepvine.__file__).resolve().parents[1]),
    }
    env.pop("GREPVINE_API_KEY", None)
    code = (
        "import grepvine as grepvine\n"
        "assert grepvine.default_client._state.resolved is None\n"
        "assert 'unresolved' in repr(grepvine.default_client)\n"
        "try:\n"
        "    grepvine.organizations.get('acme')\n"
        "except grepvine.ConfigurationError as exc:\n"
        "    assert 'mode 0600' in str(exc), exc\n"
        "else:\n"
        "    raise SystemExit('expected a configuration error')\n"
    )
    subprocess.run([sys.executable, "-c", code], env=env, check=True)


def test_configure_rebinds_existing_resources(fake: FakeGrepvine) -> None:
    fake.add_organization("acme")
    client = Client(
        api_key="gvk_wrong",
        endpoint="http://grepvine.test",
        transport=httpx.MockTransport(fake.handle),
        env={},
    )
    organizations = client.organizations
    with pytest.raises(grepvine.AuthenticationError):
        organizations.get("acme")

    client.configure(api_key=API_KEY)

    assert organizations.get("acme").name == "acme"
    assert client.config.api_key == API_KEY
    assert repr(client) == "<grepvine.Client endpoint='http://grepvine.test/v1'>"


def test_configure_none_returns_to_the_chain(tmp_path: Path) -> None:
    client = Client(
        api_key="explicit", env={"GREPVINE_API_KEY": "from-env"}, config_path=tmp_path / "none"
    )
    assert client.config.api_key == "explicit"
    client.configure(api_key=None)
    assert client.config.api_key == "from-env"
    client.configure(endpoint="http://other:8080/")
    assert client.config.endpoint == "http://other:8080/v1"
    client.configure(endpoint=None)
    assert client.config.endpoint == "https://api.grepvine.ai/v1"
    client.configure(timeout=3.5)
    assert client.config.timeout == httpx.Timeout(3.5)
    client.configure(retry=grepvine.RetryPolicy(max_attempts=1))
    assert client.config.retry.max_attempts == 1
    client.configure(retry=None)
    assert client.config.retry == grepvine.RetryPolicy()
    client.configure(config_path=tmp_path / "elsewhere")
    assert client.config.config_path == tmp_path / "elsewhere"


def test_close_then_configure_rearms(fake: FakeGrepvine) -> None:
    fake.add_organization("acme")
    client = Client(
        api_key=API_KEY,
        endpoint="http://grepvine.test",
        transport=httpx.MockTransport(fake.handle),
        env={},
    )
    with client:
        client.organizations.get("acme")
    with pytest.raises(RuntimeError, match="closed"):
        client.organizations.get("acme")
    client.configure()
    assert client.organizations.get("acme").name == "acme"
    client.close()
    client.close()


def test_missing_api_key_is_reported_on_first_request(tmp_path: Path) -> None:
    client = Client(endpoint="http://grepvine.test", env={}, config_path=tmp_path / "missing.yaml")
    with pytest.raises(ConfigurationError, match="gv login"):
        client.organizations.get("acme")


def test_default_configure_roundtrip() -> None:
    before = grepvine.default_client._state.resolved
    try:
        grepvine.configure(api_key="gvk_temporary", endpoint="http://example.test")
        assert grepvine.default_client.config.api_key == "gvk_temporary"
        assert grepvine.default_client.config.endpoint == "http://example.test/v1"
    finally:
        grepvine.configure(api_key=None, endpoint=None)
    assert grepvine.default_client._state.resolved is None
    assert before is None or before is not None
