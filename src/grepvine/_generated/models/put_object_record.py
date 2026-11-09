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
    """One document of a batch to store.

    Attributes:
        key (str): The document's key: a UTF-8, POSIX-style path of at most 1,024 bytes, with no empty, `.` or `..`
            components. Storing a key that exists replaces that document.
        content (str): The document text. A batch carries text only, so every document it stores is searchable.
        metadata (Metadata): Document metadata as a request sends it. Values are plain or tagged.
        if_match (str): A revision. The document is stored only if it still has this revision; otherwise its result has
            the error `precondition_failed`.
        if_none_match (Literal['*']): Set to `*` to store the document only if no document has this key yet; otherwise
            its result has the error `precondition_failed`.
    """

    key: str
    content: str
    metadata: Metadata | None = None
    if_match: str | None = None
    if_none_match: Literal["*"] | None = None

    def to_dict(self) -> dict[str, Any]:
        key = self.key
        content = self.content
        _metadata_value = UNSET if self.metadata is None else self.metadata
        metadata: dict[str, Any] | Unset = UNSET
        if not isinstance(_metadata_value, Unset):
            metadata = _metadata_value.to_dict()
        _if_match_value = UNSET if self.if_match is None else self.if_match
        if_match = _if_match_value
        _if_none_match_value = UNSET if self.if_none_match is None else self.if_none_match
        if_none_match = _if_none_match_value

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
            metadata=(None if isinstance(metadata, Unset) else metadata),
            if_match=(None if isinstance(if_match, Unset) else if_match),
            if_none_match=(None if isinstance(if_none_match, Unset) else if_none_match),
        )

        return put_object_record
