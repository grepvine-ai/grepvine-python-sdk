from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, TYPE_CHECKING

from attrs import define as _attrs_define


from typing import cast

if TYPE_CHECKING:
    from ..models.document_summary import DocumentSummary
    from ..models.pagination import Pagination


T = TypeVar("T", bound="DocumentPage")


@_attrs_define
class DocumentPage:
    """
    Attributes:
        results (list[DocumentSummary]):
        common_prefixes (list[str]):
        pagination (Pagination): A page may hold fewer results than the requested amount, possibly none, while has_next
            is true; a query page stops at the server's soft time budget and next_page_id resumes exactly after the last
            candidate it examined. Clients continue while has_next is true.
    """

    results: list[DocumentSummary]
    common_prefixes: list[str]
    pagination: Pagination

    def to_dict(self) -> dict[str, Any]:
        results = []
        for results_item_data in self.results:
            results_item = results_item_data.to_dict()
            results.append(results_item)

        common_prefixes = self.common_prefixes

        pagination = self.pagination.to_dict()

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "results": results,
                "common_prefixes": common_prefixes,
                "pagination": pagination,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.document_summary import DocumentSummary  # noqa: PLC0415
        from ..models.pagination import Pagination  # noqa: PLC0415

        d = dict(src_dict)
        results = []
        _results = d.pop("results")
        for results_item_data in _results:
            results_item = DocumentSummary.from_dict(results_item_data)

            results.append(results_item)

        common_prefixes = cast(list[str], d.pop("common_prefixes"))

        pagination = Pagination.from_dict(d.pop("pagination"))

        document_page = cls(
            results=results,
            common_prefixes=common_prefixes,
            pagination=pagination,
        )

        return document_page
