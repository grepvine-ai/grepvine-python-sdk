from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, TYPE_CHECKING

from attrs import define as _attrs_define
from attrs import field as _attrs_field


from ..models.usage_resolution import UsageResolution

if TYPE_CHECKING:
    from ..models.storage_usage import StorageUsage
    from ..models.usage_bucket import UsageBucket


T = TypeVar("T", bound="OrganizationUsage")


@_attrs_define
class OrganizationUsage:
    """What an organization, or one of its indexes, stores and the requests it makes, by bucket.

    Attributes:
        resolution (UsageResolution): The length of a usage bucket.
        current (StorageUsage): What is stored now: the documents and their total size, as uploaded. Metadata is not
            counted.
        buckets (list[UsageBucket]): One bucket per hour, day or month of the window, oldest first, each present even
            with no activity; the window starts no earlier than the bucket the organization was created in. The last bucket
            is the current one and is still filling.
    """

    resolution: UsageResolution
    current: StorageUsage
    buckets: list[UsageBucket]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        resolution = self.resolution.value
        current = self.current.to_dict()
        buckets = []
        for buckets_item_data in self.buckets:
            buckets_item = buckets_item_data.to_dict()
            buckets.append(buckets_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "resolution": resolution,
                "current": current,
                "buckets": buckets,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.storage_usage import StorageUsage  # noqa: PLC0415
        from ..models.usage_bucket import UsageBucket  # noqa: PLC0415

        d = dict(src_dict)
        resolution = UsageResolution(d.pop("resolution"))

        current = StorageUsage.from_dict(d.pop("current"))

        buckets = []
        _buckets = d.pop("buckets")
        for buckets_item_data in _buckets:
            buckets_item = UsageBucket.from_dict(buckets_item_data)

            buckets.append(buckets_item)

        organization_usage = cls(
            resolution=resolution,
            current=current,
            buckets=buckets,
        )

        organization_usage.additional_properties = d
        return organization_usage

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
