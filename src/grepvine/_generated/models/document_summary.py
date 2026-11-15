from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, TYPE_CHECKING

from attrs import define as _attrs_define
from attrs import field as _attrs_field


import datetime

if TYPE_CHECKING:
    from ..models.tagged_metadata import TaggedMetadata


T = TypeVar("T", bound="DocumentSummary")


@_attrs_define
class DocumentSummary:
    """A document as a listing returns it, without its content.

    Attributes:
        key (str): The document's key.
        revision (str): The document's current revision, an opaque value that changes on every write. Pass it as If-
            Match to write only if nothing changed since.
        content_bytes (int): The size of the document's content, in bytes.
        metadata (TaggedMetadata): Document metadata as a response returns it. Every value is tagged with its type.
        updated_at (datetime.datetime): When the document's current revision was stored.
        searchable (bool): Whether a search can match this document. False for content that is not valid UTF-8 or is
            over 100 MiB; such a document is stored and served but never returned by a query.
    """

    key: str
    revision: str
    content_bytes: int
    metadata: TaggedMetadata
    updated_at: datetime.datetime
    searchable: bool
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        key = self.key
        revision = self.revision
        content_bytes = self.content_bytes
        metadata = self.metadata.to_dict()
        updated_at = self.updated_at.isoformat()
        searchable = self.searchable

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
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
        from ..models.tagged_metadata import TaggedMetadata  # noqa: PLC0415

        d = dict(src_dict)
        key = d.pop("key")

        revision = d.pop("revision")

        content_bytes = d.pop("content_bytes")

        metadata = TaggedMetadata.from_dict(d.pop("metadata"))

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

        document_summary.additional_properties = d
        return document_summary

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
