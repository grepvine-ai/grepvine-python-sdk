from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, TYPE_CHECKING

from attrs import define as _attrs_define
import json
from .. import types

from ..types import UNSET, Unset

from ..types import File
from io import BytesIO

if TYPE_CHECKING:
    from ..models.metadata import Metadata


T = TypeVar("T", bound="PutDocumentForm")


@_attrs_define
class PutDocumentForm:
    """
    Attributes:
        key (str):
        content (File): The document bytes, at most 1 GiB. Valid UTF-8 of at most 100 MiB is searchable; other content
            is stored without being searchable.
        metadata (Metadata | Unset):
    """

    key: str
    content: File
    metadata: Metadata | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        key = self.key

        content = self.content.to_tuple()

        metadata: dict[str, Any] | Unset = UNSET
        if not isinstance(self.metadata, Unset):
            metadata = self.metadata.to_dict()

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
            files.append(
                (
                    "metadata",
                    (None, json.dumps(self.metadata.to_dict()).encode(), "application/json"),
                )
            )

        return files

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.metadata import Metadata  # noqa: PLC0415

        d = dict(src_dict)
        key = d.pop("key")

        content = File(payload=BytesIO(d.pop("content")))

        _metadata = d.pop("metadata", UNSET)
        metadata: Metadata | Unset
        if isinstance(_metadata, Unset):
            metadata = UNSET
        else:
            metadata = Metadata.from_dict(_metadata)

        put_document_form = cls(
            key=key,
            content=content,
            metadata=metadata,
        )

        return put_document_form
