from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, TYPE_CHECKING

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..models.index_state import IndexState
from uuid import UUID
import datetime

if TYPE_CHECKING:
    from ..models.index_tags import IndexTags


T = TypeVar("T", bound="Index")


@_attrs_define
class Index:
    """An index as a read of that one index returns it, which adds the progress of its background optimization.

    Attributes:
        id (UUID):
        organization (str): An account or organization name. Accounts and organizations share one namespace. A name
            keeps the case it was created with, and any spelling that differs only in case refers to it; no other account or
            organization can take such a spelling.
        name (str): An index name, unique in its organization. A name keeps the case it was created with, and any
            spelling that differs only in case refers to it; no other index in the organization can take such a spelling.
        canonical_id (str):
        description (str): What the index holds, in Markdown. Empty when no description was set. Clients render it
            without raw HTML.
        tags (IndexTags): Key/value labels on the index, for example the commit it was synced from. At most 64 tags. A
            key is 1 to 128 characters without whitespace or control characters; a value is at most 1,024 characters without
            control characters. Empty when none was set.
        state (IndexState):
        document_count (int):
        content_bytes (int):
        created_at (datetime.datetime):
        last_updated_at (datetime.datetime | Unset):
        optimization_progress_percent (int | Unset): How far the background optimization of this index has progressed,
            as a percentage. Omitted when no optimization is running.
    """

    id: UUID
    organization: str
    name: str
    canonical_id: str
    description: str
    tags: IndexTags
    state: IndexState
    document_count: int
    content_bytes: int
    created_at: datetime.datetime
    last_updated_at: datetime.datetime | Unset = UNSET
    optimization_progress_percent: int | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        organization = self.organization

        name = self.name

        canonical_id = self.canonical_id

        description = self.description

        tags = self.tags.to_dict()

        state = self.state.value

        document_count = self.document_count

        content_bytes = self.content_bytes

        created_at = self.created_at.isoformat()

        last_updated_at: str | Unset = UNSET
        if not isinstance(self.last_updated_at, Unset):
            last_updated_at = self.last_updated_at.isoformat()

        optimization_progress_percent = self.optimization_progress_percent

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "organization": organization,
                "name": name,
                "canonical_id": canonical_id,
                "description": description,
                "tags": tags,
                "state": state,
                "document_count": document_count,
                "content_bytes": content_bytes,
                "created_at": created_at,
            }
        )
        if last_updated_at is not UNSET:
            field_dict["last_updated_at"] = last_updated_at
        if optimization_progress_percent is not UNSET:
            field_dict["optimization_progress_percent"] = optimization_progress_percent

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.index_tags import IndexTags  # noqa: PLC0415

        d = dict(src_dict)
        id = UUID(d.pop("id"))

        organization = d.pop("organization")

        name = d.pop("name")

        canonical_id = d.pop("canonical_id")

        description = d.pop("description")

        tags = IndexTags.from_dict(d.pop("tags"))

        state = IndexState(d.pop("state"))

        document_count = d.pop("document_count")

        content_bytes = d.pop("content_bytes")

        created_at = datetime.datetime.fromisoformat(d.pop("created_at"))

        _last_updated_at = d.pop("last_updated_at", UNSET)
        last_updated_at: datetime.datetime | Unset
        if isinstance(_last_updated_at, Unset):
            last_updated_at = UNSET
        else:
            last_updated_at = datetime.datetime.fromisoformat(_last_updated_at)

        optimization_progress_percent = d.pop("optimization_progress_percent", UNSET)

        index = cls(
            id=id,
            organization=organization,
            name=name,
            canonical_id=canonical_id,
            description=description,
            tags=tags,
            state=state,
            document_count=document_count,
            content_bytes=content_bytes,
            created_at=created_at,
            last_updated_at=last_updated_at,
            optimization_progress_percent=optimization_progress_percent,
        )

        index.additional_properties = d
        return index

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
