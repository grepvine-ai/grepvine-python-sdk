from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from .. import types

from ..types import UNSET, Unset

from ..types import File
from io import BytesIO


T = TypeVar("T", bound="PutDocumentForm")


@_attrs_define
class PutDocumentForm:
    """
    Attributes:
        key (str):
        content (File): The document bytes, at most 1 GiB. Valid UTF-8 of at most 100 MiB is searchable; other content
            is stored without being searchable.
        metadata (str | Unset): A Metadata JSON object.
    """

    key: str
    content: File
    metadata: str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        key = self.key

        content = self.content.to_tuple()

        metadata = self.metadata

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "key": key,
                "content": content,
            }
        )
        if metadata is not UNSET:
            field_dict["metadata"] = metadata

        return field_dict

    def to_multipart(self) -> types.RequestFiles:
        files: types.RequestFiles = []

        files.append(("key", (None, str(self.key).encode(), "text/plain")))

        files.append(("content", self.content.to_tuple()))

        if not isinstance(self.metadata, Unset):
            files.append(("metadata", (None, str(self.metadata).encode(), "text/plain")))

        return files

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        key = d.pop("key")

        content = File(payload=BytesIO(d.pop("content")))

        metadata = d.pop("metadata", UNSET)

        put_document_form = cls(
            key=key,
            content=content,
            metadata=metadata,
        )

        return put_document_form
