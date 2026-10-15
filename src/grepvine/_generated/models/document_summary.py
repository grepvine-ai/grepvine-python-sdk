from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, TYPE_CHECKING

from attrs import define as _attrs_define


import datetime

if TYPE_CHECKING:
    from ..models.metadata import Metadata


T = TypeVar("T", bound="DocumentSummary")


@_attrs_define
class DocumentSummary:
    """
    Attributes:
        key (str):
        revision (str):
        content_bytes (int):
        metadata (Metadata):
        updated_at (datetime.datetime): When the document's current revision was stored.
        searchable (bool): Whether a search can match this document. False for content that is not valid UTF-8 or is
            over 100 MiB; such a document is stored and served but never returned by a query.
    """

    key: str
    revision: str
    content_bytes: int
    metadata: Metadata
    updated_at: datetime.datetime
    searchable: bool

    def to_dict(self) -> dict[str, Any]:
        key = self.key

        revision = self.revision

        content_bytes = self.content_bytes

        metadata = self.metadata.to_dict()

        updated_at = self.updated_at.isoformat()

        searchable = self.searchable

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "key": key,
                "revision": revision,
                "content_bytes": content_bytes,
                "metadata": metadata,
                "updated_at": updated_at,
                "searchable": searchable,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.metadata import Metadata  # noqa: PLC0415

        d = dict(src_dict)
        key = d.pop("key")

        revision = d.pop("revision")

        content_bytes = d.pop("content_bytes")

        metadata = Metadata.from_dict(d.pop("metadata"))

        updated_at = datetime.datetime.fromisoformat(d.pop("updated_at"))

        searchable = d.pop("searchable")

        document_summary = cls(
            key=key,
            revision=revision,
            content_bytes=content_bytes,
            metadata=metadata,
            updated_at=updated_at,
            searchable=searchable,
        )

        return document_summary
