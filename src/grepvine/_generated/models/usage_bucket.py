from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, TYPE_CHECKING

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

import datetime

if TYPE_CHECKING:
    from ..models.usage_requests import UsageRequests


T = TypeVar("T", bound="UsageBucket")


@_attrs_define
class UsageBucket:
    """Usage in one hour, day or month.

    Attributes:
        start (datetime.datetime): When the bucket starts, in UTC.
        requests (UsageRequests): The successful requests in a bucket, by operation. A request that was refused or
            failed is not counted. An API request and an MCP tool call each count once; a batch counts once.
        documents (int): The average number of documents stored during the bucket, rounded down. Storage is measured
            once an hour; this is absent when it was not measured in any hour of the bucket, such as the current hour before
            its measurement.
        stored_bytes (int): The average size of the documents stored during the bucket, in bytes, rounded down: the size
            measured in each hour of the bucket, an index that did not exist counting as zero, divided by the hours
            measured. Documents stored and deleted within the same hour are not seen. Absent when no hour of the bucket was
            measured.
    """

    start: datetime.datetime
    requests: UsageRequests
    documents: int | None = None
    stored_bytes: int | None = None
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        start = self.start.isoformat()
        requests = self.requests.to_dict()
        _documents_value = UNSET if self.documents is None else self.documents
        documents = _documents_value
        _stored_bytes_value = UNSET if self.stored_bytes is None else self.stored_bytes
        stored_bytes = _stored_bytes_value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "start": start,
                "requests": requests,
            }
        )
        if documents is not UNSET:
            field_dict["documents"] = documents
        if stored_bytes is not UNSET:
            field_dict["stored_bytes"] = stored_bytes

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.usage_requests import UsageRequests  # noqa: PLC0415

        d = dict(src_dict)
        start = datetime.datetime.fromisoformat(d.pop("start"))

        requests = UsageRequests.from_dict(d.pop("requests"))

        documents = d.pop("documents", UNSET)

        stored_bytes = d.pop("stored_bytes", UNSET)

        usage_bucket = cls(
            start=start,
            requests=requests,
            documents=(None if isinstance(documents, Unset) else documents),
            stored_bytes=(None if isinstance(stored_bytes, Unset) else stored_bytes),
        )

        usage_bucket.additional_properties = d
        return usage_bucket

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
