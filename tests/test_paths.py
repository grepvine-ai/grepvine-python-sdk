from __future__ import annotations

import pytest

from grepvine_sdk._core import paths


def test_parse_index_ref() -> None:
    assert paths.parse_index_ref("acme/docs") == ("acme", "docs")
    for bad in ["acme", "acme/", "/docs", "a/b/c", ""]:
        with pytest.raises(ValueError, match="ORGANIZATION/INDEX"):
            paths.parse_index_ref(bad)


def test_check_key() -> None:
    assert paths.check_key("src/main.go") == "src/main.go"
    with pytest.raises(ValueError, match="must not be empty"):
        paths.check_key("")
    with pytest.raises(ValueError, match="at most 1024"):
        paths.check_key("k" * 1025)
