from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, TYPE_CHECKING

from attrs import define as _attrs_define

from ..types import UNSET, Unset


if TYPE_CHECKING:
    from ..models.index_tag_changes import IndexTagChanges


T = TypeVar("T", bound="UpdateIndexRequest")


@_attrs_define
class UpdateIndexRequest:
    """The fields to change. A field that is absent is left as it is; at least one must be present.

    Attributes:
        description (str | Unset): What the index holds, in Markdown. Empty when no description was set. Clients render
            it without raw HTML.
        tags (IndexTagChanges | Unset): Tags to set, by key, and tags to remove, given as null. A key absent from the
            map is unchanged.
    """

    description: str | Unset = UNSET
    tags: IndexTagChanges | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        description = self.description

        tags: dict[str, Any] | Unset = UNSET
        if not isinstance(self.tags, Unset):
            tags = self.tags.to_dict()

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if description is not UNSET:
            field_dict["description"] = description
        if tags is not UNSET:
            field_dict["tags"] = tags

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.index_tag_changes import IndexTagChanges  # noqa: PLC0415

        d = dict(src_dict)
        description = d.pop("description", UNSET)

        _tags = d.pop("tags", UNSET)
        tags: IndexTagChanges | Unset
        if isinstance(_tags, Unset):
            tags = UNSET
        else:
            tags = IndexTagChanges.from_dict(_tags)

        update_index_request = cls(
            description=description,
            tags=tags,
        )

        return update_index_request
