"""Data returned by the Grepvine API.

Every model is an immutable dataclass named after the API's schema, with field
names that match the API. A few carry the names the Python SDK has always used:
:class:`IndexData` is the API's ``Index``, :class:`SearchResult` its
``QueryResult``, and :class:`DocumentError` the ``error`` of a
:class:`MutationResult`. Parsers ignore fields they do not know, so a newer
service does not break an older SDK.
"""

from __future__ import annotations

from bisect import bisect_left
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import datetime
from itertools import accumulate
from typing import Any, Generic, Literal, NamedTuple, Protocol, TypeAlias, TypeVar

from grepvine._core.metadata import untag

__all__ = [
    "APIKey",
    "APIKeyCreated",
    "ContentRange",
    "ContextLine",
    "Document",
    "DocumentError",
    "DeviceAuthorization",
    "DocumentSummary",
    "IndexData",
    "IndexState",
    "Match",
    "Member",
    "MutationResult",
    "Organization",
    "Page",
    "Role",
    "SearchResult",
    "Span",
    "User",
]

T = TypeVar("T")
M = TypeVar("M")


class _APIModel(Protocol):
    def to_dict(self) -> dict[str, Any]: ...


def from_api(cls: Callable[[Mapping[str, Any]], M], model: _APIModel) -> M:
    """Convert a decoded API model into its SDK model through its wire form."""
    return cls(model.to_dict())


Role: TypeAlias = Literal["owner", "admin", "developer", "reader"]
"""The caller's role in an organization."""

IndexState: TypeAlias = Literal["creating", "ready", "deleting", "delete_failed"]
"""The lifecycle state of an index."""


def _datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value))


def _optional_datetime(value: Any) -> datetime | None:
    return None if value is None else _datetime(value)


@dataclass(frozen=True, slots=True, kw_only=True)
class Organization:
    """An organization the API key can see, with the caller's role in it."""

    id: str
    name: str
    role: str
    created_at: datetime

    @classmethod
    def _from_json(cls, data: Mapping[str, Any]) -> Organization:
        return cls(
            id=str(data["id"]),
            name=str(data["name"]),
            role=str(data["role"]),
            created_at=_datetime(data["created_at"]),
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class User:
    """A user account."""

    id: str
    name: str
    email: str
    created_at: datetime

    @classmethod
    def _from_json(cls, data: Mapping[str, Any]) -> User:
        return cls(
            id=str(data["id"]),
            name=str(data["name"]),
            email=str(data["email"]),
            created_at=_datetime(data["created_at"]),
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class Member:
    """A member of an organization and their role in it."""

    user: User
    role: str
    created_at: datetime

    @classmethod
    def _from_json(cls, data: Mapping[str, Any]) -> Member:
        return cls(
            user=User._from_json(data["user"]),
            role=str(data["role"]),
            created_at=_datetime(data["created_at"]),
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class APIKey:
    """An API key of the current user. The secret itself is shown only once, at creation."""

    id: str
    name: str
    prefix: str
    created_at: datetime
    last_used_at: datetime | None = None
    revoked_at: datetime | None = None

    @property
    def revoked(self) -> bool:
        """Whether the key has been revoked."""
        return self.revoked_at is not None

    @classmethod
    def _from_json(cls, data: Mapping[str, Any]) -> APIKey:
        return cls(**_api_key_fields(data))


@dataclass(frozen=True, slots=True, kw_only=True)
class APIKeyCreated(APIKey):
    """A newly issued API key together with its secret ``key``, which is not shown again."""

    key: str

    def __repr__(self) -> str:
        return f"APIKeyCreated(id={self.id!r}, name={self.name!r}, prefix={self.prefix!r})"

    @classmethod
    def _from_json(cls, data: Mapping[str, Any]) -> APIKeyCreated:
        return cls(**_api_key_fields(data), key=str(data["key"]))


def _api_key_fields(data: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "id": str(data["id"]),
        "name": str(data["name"]),
        "prefix": str(data["prefix"]),
        "created_at": _datetime(data["created_at"]),
        "last_used_at": _optional_datetime(data.get("last_used_at")),
        "revoked_at": _optional_datetime(data.get("revoked_at")),
    }


@dataclass(frozen=True, slots=True, kw_only=True)
class DeviceAuthorization:
    """A device login in progress.

    Show ``user_code`` and ``verification_uri`` (or ``verification_uri_complete``,
    which carries the code) to the person approving the login. The login
    expires after ``expires_in`` seconds; poll for the key no more often than
    every ``interval`` seconds.
    """

    device_code: str
    user_code: str
    verification_uri: str
    verification_uri_complete: str
    expires_in: int
    interval: int

    def __repr__(self) -> str:
        return (
            f"DeviceAuthorization(user_code={self.user_code!r}, "
            f"verification_uri={self.verification_uri!r}, expires_in={self.expires_in})"
        )

    @classmethod
    def _from_json(cls, data: Mapping[str, Any]) -> DeviceAuthorization:
        return cls(
            device_code=str(data["device_code"]),
            user_code=str(data["user_code"]),
            verification_uri=str(data["verification_uri"]),
            verification_uri_complete=str(data["verification_uri_complete"]),
            expires_in=int(data["expires_in"]),
            interval=int(data["interval"]),
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class IndexData:
    """The fields of an index as the API reports them.

    ``document_count`` and the other counters are a snapshot from the time the
    index was fetched. ``description`` is Markdown, and empty when none was set.
    ``tags`` are the index's key/value labels as of the same moment, empty when
    none was set; change them through ``update(tags=...)`` on a handle.
    """

    id: str
    organization: str
    name: str
    canonical_id: str
    state: str
    document_count: int
    content_bytes: int
    created_at: datetime
    description: str = ""
    tags: Mapping[str, str] = field(default_factory=dict, hash=False)
    last_updated_at: datetime | None = None
    optimization_progress_percent: int | None = None

    @property
    def ref(self) -> str:
        """The ``organization/name`` reference of this index."""
        return f"{self.organization}/{self.name}"

    @classmethod
    def _from_json(cls, data: Mapping[str, Any]) -> IndexData:
        progress = data.get("optimization_progress_percent")
        return cls(
            id=str(data["id"]),
            organization=str(data["organization"]),
            name=str(data["name"]),
            canonical_id=str(data["canonical_id"]),
            state=str(data["state"]),
            document_count=int(data["document_count"]),
            content_bytes=int(data["content_bytes"]),
            created_at=_datetime(data["created_at"]),
            description=str(data.get("description") or ""),
            tags=dict(data.get("tags") or {}),
            last_updated_at=_optional_datetime(data.get("last_updated_at")),
            optimization_progress_percent=None if progress is None else int(progress),
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class DocumentError:
    """Why a list-form write left one document unchanged.

    ``code`` says why in machine-readable form: ``"precondition_failed"`` when
    the document's ``if_match`` or ``if_none_match`` condition did not hold, and
    ``"not_found"`` when a document to delete does not exist. ``message`` is
    the service's sentence about it. The three fields mean what they mean on
    :class:`~grepvine.errors.APIError`.
    """

    code: str
    reason: str
    message: str

    def __str__(self) -> str:
        return f"{self.message} ({self.code})"

    @classmethod
    def _from_optional_json(cls, data: Any) -> DocumentError | None:
        if not isinstance(data, Mapping):
            return None
        code, reason, message = data.get("code"), data.get("reason"), data.get("error")
        return cls(
            code=str(code) if code else "request_failed",
            reason=str(reason) if reason else "",
            message=str(message) if message else "the document was not changed",
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class MutationResult:
    """The outcome of storing or deleting one document.

    A document that was stored or deleted has its new ``revision`` and no
    ``error``. In the list forms of ``put`` and ``delete``, every document has a
    result; one the write left unchanged has an ``error`` saying why, and no
    revision. The single-document forms raise the matching
    :class:`~grepvine.errors.APIError` instead.
    """

    key: str
    revision: str | None = None
    error: DocumentError | None = None

    @property
    def ok(self) -> bool:
        """Whether the document was stored or deleted."""
        return self.error is None

    @classmethod
    def _from_json(cls, data: Mapping[str, Any]) -> MutationResult:
        revision = data.get("revision")
        return cls(
            key=str(data["key"]),
            revision=str(revision) if revision else None,
            error=DocumentError._from_optional_json(data.get("error")),
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class DocumentSummary:
    """One entry of a document listing."""

    key: str
    revision: str
    content_bytes: int
    metadata: dict[str, Any]
    updated_at: datetime
    searchable: bool

    @property
    def size(self) -> int:
        """The document's size in bytes."""
        return self.content_bytes

    @classmethod
    def _from_json(cls, data: Mapping[str, Any]) -> DocumentSummary:
        return cls(
            key=str(data["key"]),
            revision=str(data["revision"]),
            content_bytes=int(data["content_bytes"]),
            metadata=untag(data.get("metadata")),
            updated_at=_datetime(data["updated_at"]),
            searchable=bool(data["searchable"]),
        )


class ContentRange(NamedTuple):
    """The byte range a partial document read covers, with the document's total size."""

    start: int
    end: int
    total: int


@dataclass(frozen=True, slots=True, kw_only=True)
class Document:
    """A document's content together with its revision and metadata."""

    key: str
    revision: str
    content: bytes
    metadata: dict[str, Any]
    content_range: ContentRange | None = None

    @property
    def size(self) -> int:
        """The size of the whole document in bytes."""
        if self.content_range is not None:
            return self.content_range.total
        return len(self.content)

    def text(self, encoding: str = "utf-8") -> str:
        """The content decoded as text."""
        return self.content.decode(encoding)

    def __bytes__(self) -> bytes:
        return self.content


@dataclass(frozen=True, slots=True, kw_only=True)
class Match:
    """One match, as a byte offset and length within the document."""

    offset: int
    length: int

    @property
    def end(self) -> int:
        return self.offset + self.length

    @classmethod
    def _from_json(cls, data: Mapping[str, Any]) -> Match:
        return cls(offset=int(data["offset"]), length=int(data["length"]))


@dataclass(frozen=True, slots=True, kw_only=True)
class ContextLine:
    """One line near a result."""

    line_number: int
    text: str
    text_truncated: bool

    @classmethod
    def _from_json(cls, data: Mapping[str, Any]) -> ContextLine:
        return cls(
            line_number=int(data["line_number"]),
            text=str(data["text"]),
            text_truncated=bool(data["text_truncated"]),
        )


class Span(NamedTuple):
    """A half-open ``[start, end)`` range of character positions in ``text``."""

    start: int
    end: int


@dataclass(frozen=True, slots=True, kw_only=True)
class SearchResult:
    """One match, or several matches that share lines, together with the lines it covers.

    Offsets and lengths reported by the API count bytes within the document.
    Use :meth:`match_spans` for character positions within :attr:`text`.
    """

    key: str
    revision: str
    line_number: int
    last_line_number: int
    line_start_offset: int
    line_end_offset: int
    text_start_offset: int
    text_line_number: int
    text: str
    matches: tuple[Match, ...]
    text_truncated: bool
    matches_truncated: bool
    lines_before: tuple[ContextLine, ...] = ()
    lines_after: tuple[ContextLine, ...] = ()

    @classmethod
    def _from_json(cls, data: Mapping[str, Any]) -> SearchResult:
        return cls(
            key=str(data["key"]),
            revision=str(data["revision"]),
            line_number=int(data["line_number"]),
            last_line_number=int(data["last_line_number"]),
            line_start_offset=int(data["line_start_offset"]),
            line_end_offset=int(data["line_end_offset"]),
            text_start_offset=int(data["text_start_offset"]),
            text_line_number=int(data["text_line_number"]),
            text=str(data["text"]),
            matches=tuple(Match._from_json(item) for item in data.get("matches") or ()),
            text_truncated=bool(data["text_truncated"]),
            matches_truncated=bool(data["matches_truncated"]),
            lines_before=tuple(
                ContextLine._from_json(item) for item in data.get("lines_before") or ()
            ),
            lines_after=tuple(
                ContextLine._from_json(item) for item in data.get("lines_after") or ()
            ),
        )

    @property
    def text_bytes(self) -> bytes:
        """The covered text as UTF-8 bytes, the unit the API's offsets count."""
        return self.text.encode("utf-8")

    @property
    def lines(self) -> list[str]:
        """The covered lines of ``text``."""
        return self.text.split("\n")

    def numbered_lines(self) -> list[tuple[int, str]]:
        """The covered lines of ``text`` paired with their one-based line numbers."""
        return list(enumerate(self.lines, start=self.text_line_number))

    def match_byte_spans(self) -> list[Span]:
        """Each match as a byte range within :attr:`text_bytes`.

        A match that consumed the last line's break extends one byte past the
        text; such a span is clipped to the text.
        """
        limit = len(self.text_bytes)
        spans: list[Span] = []
        for match in self.matches:
            start = min(max(match.offset - self.text_start_offset, 0), limit)
            end = min(max(match.end - self.text_start_offset, 0), limit)
            spans.append(Span(start, end))
        return spans

    def match_spans(self) -> list[Span]:
        """Each match as a character range within :attr:`text`, ready for slicing."""
        starts = list(accumulate((len(char.encode("utf-8")) for char in self.text), initial=0))
        return [
            Span(bisect_left(starts, span.start), bisect_left(starts, span.end))
            for span in self.match_byte_spans()
        ]

    def match_texts(self) -> list[str]:
        """The matched text of each match."""
        return [self.text[span.start : span.end] for span in self.match_spans()]


@dataclass(frozen=True, slots=True, kw_only=True)
class Page(Generic[T]):
    """One page of results.

    Pass ``next_page_id`` back as ``page`` and ``page_size`` as ``page_size``,
    with every other argument unchanged, to continue from this page. A token is
    valid for 15 minutes.
    """

    results: tuple[T, ...]
    next_page_id: str | None
    has_next: bool
    page_size: int
    common_prefixes: tuple[str, ...] = ()

    @classmethod
    def _from_json(
        cls, data: Mapping[str, Any], item: Callable[[Mapping[str, Any]], T], page_size: int
    ) -> Page[T]:
        pagination = data.get("pagination") or {}
        has_next = bool(pagination.get("has_next"))
        token = pagination.get("next_page_id") or None
        return cls(
            results=tuple(item(entry) for entry in data.get("results") or ()),
            next_page_id=str(token) if has_next and token else None,
            has_next=has_next,
            page_size=page_size,
            common_prefixes=tuple(str(prefix) for prefix in data.get("common_prefixes") or ()),
        )
