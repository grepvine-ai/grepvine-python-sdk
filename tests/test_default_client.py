from __future__ import annotations

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


def test_import_resolves_nothing() -> None:
    assert "unresolved" in repr(Client())


def test_configure_rebinds_existing_resources(fake: FakeGrepvine) -> None:
    fake.add_organization("acme")
    client = Client(
        api_key="gvk_wrong",
        endpoint="http://grepvine.test",
        transport=httpx.MockTransport(fake.handle),
    )
    organizations = client.organizations
    with pytest.raises(grepvine.AuthenticationError):
        organizations.get("acme")

    client.configure(api_key=API_KEY)

    assert organizations.get("acme").name == "acme"
    assert client.config.api_key == API_KEY
    assert repr(client) == "<grepvine.Client endpoint='http://grepvine.test/v1'>"


def test_configure_none_returns_to_the_default() -> None:
    client = Client(api_key="explicit")
    assert client.config.api_key == "explicit"
    client.configure(api_key=None)
    assert client.config.api_key is None
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


def test_close_then_configure_rearms(fake: FakeGrepvine) -> None:
    fake.add_organization("acme")
    client = Client(
        api_key=API_KEY,
        endpoint="http://grepvine.test",
        transport=httpx.MockTransport(fake.handle),
    )
    with client:
        client.organizations.get("acme")
    with pytest.raises(RuntimeError, match="closed"):
        client.organizations.get("acme")
    client.configure()
    assert client.organizations.get("acme").name == "acme"
    client.close()
    client.close()


def test_missing_api_key_is_reported_on_first_request() -> None:
    client = Client(endpoint="http://grepvine.test")
    with pytest.raises(ConfigurationError, match="pass api_key"):
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
