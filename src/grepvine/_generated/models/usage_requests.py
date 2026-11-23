from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field


T = TypeVar("T", bound="UsageRequests")


@_attrs_define
class UsageRequests:
    """The successful requests in a bucket, by operation. A request that was refused or failed is not counted. An API
    request and an MCP tool call each count once; a batch counts once.

        Attributes:
            search (int): Searches.
            read (int): Document reads and listings.
            write (int): Document writes and deletions.
            manage (int): Every other request on the organization or its indexes, such as reading or changing an index or
                the members.
            total (int): All of them.
    """

    search: int
    read: int
    write: int
    manage: int
    total: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        search = self.search
        read = self.read
        write = self.write
        manage = self.manage
        total = self.total

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "search": search,
                "read": read,
                "write": write,
                "manage": manage,
                "total": total,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        search = d.pop("search")

        read = d.pop("read")

        write = d.pop("write")

        manage = d.pop("manage")

        total = d.pop("total")

        usage_requests = cls(
            search=search,
            read=read,
            write=write,
            manage=manage,
            total=total,
        )

        usage_requests.additional_properties = d
        return usage_requests

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
