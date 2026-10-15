"""Parsing of ``organization/index`` references and document key limits."""

from __future__ import annotations

from typing import Final

MAX_KEY_LENGTH: Final = 1024


def parse_index_ref(ref: str) -> tuple[str, str]:
    """Split ``"organization/index"`` into its two names.

    Mirrors the ``gv`` command-line client: the reference is split at the first
    slash, both halves must be present, and the index half may not contain a
    slash.
    """
    organization, separator, index = ref.partition("/")
    if not separator or not organization or not index or "/" in index:
        raise ValueError("index must be ORGANIZATION/INDEX")
    return organization, index


def check_key(key: str) -> str:
    """Check a document key: 1 to 1,024 characters."""
    if not key:
        raise ValueError("document key must not be empty")
    if len(key) > MAX_KEY_LENGTH:
        raise ValueError(f"document key must be at most {MAX_KEY_LENGTH} characters")
    return key
