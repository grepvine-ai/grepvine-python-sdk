from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, TYPE_CHECKING

from attrs import define as _attrs_define

from ..types import UNSET, Unset


if TYPE_CHECKING:
    from ..models.index_tags import IndexTags


T = TypeVar("T", bound="CreateIndexRequest")


@_attrs_define
class CreateIndexRequest:
    """
    Attributes:
        name (str): An index name, unique in its organization. A name keeps the case it was created with, and any
            spelling that differs only in case refers to it; no other index in the organization can take such a spelling.
        description (str | Unset): What the index holds, in Markdown. Empty when no description was set. Clients render
            it without raw HTML.
        tags (IndexTags | Unset): Key/value labels on the index, for example the commit it was synced from. At most 64
            tags. A key is 1 to 128 characters without whitespace or control characters; a value is at most 1,024 characters
            without control characters. Empty when none was set.
    """

    name: str
    description: str | Unset = UNSET
    tags: IndexTags | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        description = self.description

        tags: dict[str, Any] | Unset = UNSET
        if not isinstance(self.tags, Unset):
            tags = self.tags.to_dict()

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "name": name,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description
        if tags is not UNSET:
            field_dict["tags"] = tags

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.index_tags import IndexTags  # noqa: PLC0415

        d = dict(src_dict)
        name = d.pop("name")

        description = d.pop("description", UNSET)

        _tags = d.pop("tags", UNSET)
        tags: IndexTags | Unset
        if isinstance(_tags, Unset):
            tags = UNSET
        else:
            tags = IndexTags.from_dict(_tags)

        create_index_request = cls(
            name=name,
            description=description,
            tags=tags,
        )

        return create_index_request
