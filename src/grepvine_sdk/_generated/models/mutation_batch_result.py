from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, TYPE_CHECKING

from attrs import define as _attrs_define


if TYPE_CHECKING:
    from ..models.mutation_result import MutationResult


T = TypeVar("T", bound="MutationBatchResult")


@_attrs_define
class MutationBatchResult:
    """
    Attributes:
        results (list[MutationResult]):
    """

    results: list[MutationResult]

    def to_dict(self) -> dict[str, Any]:
        results = []
        for results_item_data in self.results:
            results_item = results_item_data.to_dict()
            results.append(results_item)

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "results": results,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.mutation_result import MutationResult  # noqa: PLC0415

        d = dict(src_dict)
        results = []
        _results = d.pop("results")
        for results_item_data in _results:
            results_item = MutationResult.from_dict(results_item_data)

            results.append(results_item)

        mutation_batch_result = cls(
            results=results,
        )

        return mutation_batch_result
