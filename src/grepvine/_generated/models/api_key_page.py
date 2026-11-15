from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, TYPE_CHECKING

from attrs import define as _attrs_define
from attrs import field as _attrs_field


if TYPE_CHECKING:
    from ..models.api_key import APIKey
    from ..models.pagination import Pagination


T = TypeVar("T", bound="APIKeyPage")


@_attrs_define
class APIKeyPage:
    """A page of API keys.

    Attributes:
        results (list[APIKey]): The API keys on this page.
        pagination (Pagination): A page may hold fewer results than the requested amount, possibly none, while has_next
            is true; a query page stops at the server's soft time budget and next_page_id resumes exactly after the last
            candidate it examined. Clients continue while has_next is true.
    """

    results: list[APIKey]
    pagination: Pagination
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        results = []
        for results_item_data in self.results:
            results_item = results_item_data.to_dict()
            results.append(results_item)

        pagination = self.pagination.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "results": results,
                "pagination": pagination,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.api_key import APIKey  # noqa: PLC0415
        from ..models.pagination import Pagination  # noqa: PLC0415

        d = dict(src_dict)
        results = []
        _results = d.pop("results")
        for results_item_data in _results:
            results_item = APIKey.from_dict(results_item_data)

            results.append(results_item)

        pagination = Pagination.from_dict(d.pop("pagination"))

        api_key_page = cls(
            results=results,
            pagination=pagination,
        )

        api_key_page.additional_properties = d
        return api_key_page

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
