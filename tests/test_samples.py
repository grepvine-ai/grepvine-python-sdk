"""Every Python block in the README and every program in examples/ runs against a fake service.

Each sample runs on its own, with a fresh FakeGrepvine (tests/fake_service.py) seeded with what
the sample's text assumes already exists, and with the client configured from the environment as
a reader's would be. A sample that names something missing, or calls in the wrong order, fails
here the way it would against the service.
"""

from __future__ import annotations

import io
import os
import re
import runpy
import sys
import urllib.request
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import httpx
import pytest

import grepvine
from tests.fake_service import FakeGrepvine

ROOT = Path(__file__).resolve().parents[1]
BLOCKS = re.findall(r"```python\n(.*?)```", (ROOT / "README.md").read_text(), re.S)
EXAMPLES = sorted((ROOT / "examples").glob("*.py"))


def first_line(block: str) -> str:
    return block.strip().splitlines()[0][:60]


class FakeResponse(io.RawIOBase):
    """A stand-in for an HTTP response that is read once, such as urlopen's."""

    def __init__(self, data: bytes) -> None:
        self._data = io.BytesIO(data)
        self.headers = {"Content-Length": str(len(data))}

    def readable(self) -> bool:
        return True

    def seekable(self) -> bool:
        return False

    def read(self, size: int = -1) -> bytes:
        return self._data.read(size)

    def __enter__(self) -> FakeResponse:
        return self

    def __exit__(self, *_: object) -> None:
        pass


@pytest.fixture
def fake(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[FakeGrepvine]:
    """A fresh service that every client of the test talks to, and a reader's environment."""
    service = FakeGrepvine()

    def mock(*_: Any, **__: Any) -> httpx.MockTransport:
        return httpx.MockTransport(service.handle)

    monkeypatch.setattr(httpx, "HTTPTransport", mock)
    monkeypatch.setattr(httpx, "AsyncHTTPTransport", mock)
    monkeypatch.setattr(
        urllib.request, "urlopen", lambda *_args, **_kw: FakeResponse(b"a,b\n1,2\n")
    )
    monkeypatch.setenv("GREPVINE_API_KEY", service.api_key)
    monkeypatch.setenv("GREPVINE_ORGANIZATION", "acme")
    monkeypatch.setenv("CI_GREPVINE_KEY", service.api_key)
    monkeypatch.chdir(tmp_path)
    (tmp_path / "out").mkdir()
    (tmp_path / "out/report.pdf").write_bytes(b"%PDF-1.7\n")
    staging = tmp_path / ".grepvine/staging.yaml"
    staging.parent.mkdir()
    staging.write_text(f"api_key: {service.api_key}\norganization: acme\n")
    staging.chmod(0o600)
    yield service


def seed(service: FakeGrepvine, block: str) -> dict[str, Any]:
    """Create what the block's text assumes exists, and the names it borrows from the README."""
    names: dict[str, Any] = {}
    if 'organizations.create(name="my-org")' not in block:
        service.orgs["my-org"] = type(service.orgs["acme"])("my-org", {"alice": "owner"})
        service.add_index("my-org", "my-index", {"videos/demo.mp4": "not really a video\n"})
    if "create(" not in block or "ConflictError" in block:
        index = service.add_index(
            "acme",
            "support",
            {
                "src/app.go": "func main() {\n\t// TODO handle connection reset by peer\n}\n",
                "notes.md": "hello world\n",
                "c.txt": "gamma\n",
                "tickets/readme.md": "tickets\n",
                "tickets/2026/T-1.md": "a ticket\n",
            },
        )
        index.documents["report.pdf"] = type(index.documents["c.txt"])(
            "report.pdf", b"%PDF", {"pages": {"type": "integer", "value": 12}}
        )
        names["revision"] = index.documents["c.txt"].revision
    return names


@pytest.mark.parametrize("block", BLOCKS, ids=[first_line(b) for b in BLOCKS])
def test_readme_block_runs(
    block: str, fake: FakeGrepvine, capsys: pytest.CaptureFixture[str]
) -> None:
    namespace: dict[str, Any] = {"__name__": "readme", **seed(fake, block)}
    namespace["grepvine"] = grepvine
    namespace["client"] = grepvine.Client()
    namespace["index"] = namespace["client"].index("acme/support")
    exec(compile(block, "README.md", "exec"), namespace)
    assert "Unset object" not in capsys.readouterr().out


@pytest.mark.parametrize("path", EXAMPLES, ids=[p.name for p in EXAMPLES])
def test_example_runs(
    path: Path,
    fake: FakeGrepvine,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(sys, "argv", [str(path)])
    runpy.run_path(str(path), run_name="__main__")
    out = capsys.readouterr().out
    assert "Unset object" not in out
    if path.name == "device_login.py":
        assert "Signed in as alice" in out


def test_every_readme_section_has_a_running_block() -> None:
    """The README's samples are what this module runs; keep them from silently disappearing."""
    assert len(BLOCKS) >= 15
    assert len(EXAMPLES) == 3
    assert os.path.exists(ROOT / "examples/device_login.py")
