from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, TYPE_CHECKING

from attrs import define as _attrs_define

from ..types import UNSET, Unset

from typing import cast
from typing import Literal

if TYPE_CHECKING:
    from ..models.metadata import Metadata


T = TypeVar("T", bound="PutObjectRecord")


@_attrs_define
class PutObjectRecord:
    """
    Attributes:
        key (str):
        content (str): The document text. A batch carries text only, so every document it stores is searchable.
        metadata (Metadata | Unset):
        if_match (str | Unset):
        if_none_match (Literal['*'] | Unset):
    """

    key: str
    content: str
    metadata: Metadata | Unset = UNSET
    if_match: str | Unset = UNSET
    if_none_match: Literal["*"] | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        key = self.key

        content = self.content

        metadata: dict[str, Any] | Unset = UNSET
        if not isinstance(self.metadata, Unset):
            metadata = self.metadata.to_dict()

        if_match = self.if_match

        if_none_match = self.if_none_match

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "key": key,
                "content": content,
            }
        )
        if metadata is not UNSET:
            field_dict["metadata"] = metadata
        if if_match is not UNSET:
            field_dict["if_match"] = if_match
        if if_none_match is not UNSET:
            field_dict["if_none_match"] = if_none_match

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.metadata import Metadata  # noqa: PLC0415

        d = dict(src_dict)
        key = d.pop("key")

        content = d.pop("content")

        _metadata = d.pop("metadata", UNSET)
        metadata: Metadata | Unset
        if isinstance(_metadata, Unset):
            metadata = UNSET
        else:
            metadata = Metadata.from_dict(_metadata)

        if_match = d.pop("if_match", UNSET)

        if_none_match = cast(Literal["*"] | Unset, d.pop("if_none_match", UNSET))
        if if_none_match != "*" and not isinstance(if_none_match, Unset):
            raise ValueError(f"if_none_match must match const '*', got '{if_none_match}'")

        put_object_record = cls(
            key=key,
            content=content,
            metadata=metadata,
            if_match=if_match,
            if_none_match=if_none_match,
        )

        return put_object_record
