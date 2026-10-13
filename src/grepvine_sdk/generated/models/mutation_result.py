from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, TYPE_CHECKING

from attrs import define as _attrs_define

from ..types import UNSET, Unset


if TYPE_CHECKING:
    from ..models.error import Error


T = TypeVar("T", bound="MutationResult")


@_attrs_define
class MutationResult:
    """The outcome of one document. A stored or deleted document has a revision; a document a batch did not change has an
    error instead.

        Attributes:
            key (str):
            revision (str | Unset):
            error (Error | Unset):
    """

    key: str
    revision: str | Unset = UNSET
    error: Error | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        key = self.key

        revision = self.revision

        error: dict[str, Any] | Unset = UNSET
        if not isinstance(self.error, Unset):
            error = self.error.to_dict()

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "key": key,
            }
        )
        if revision is not UNSET:
            field_dict["revision"] = revision
        if error is not UNSET:
            field_dict["error"] = error

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.error import Error  # noqa: PLC0415

        d = dict(src_dict)
        key = d.pop("key")

        revision = d.pop("revision", UNSET)

        _error = d.pop("error", UNSET)
        error: Error | Unset
        if isinstance(_error, Unset):
            error = UNSET
        else:
            error = Error.from_dict(_error)

        mutation_result = cls(
            key=key,
            revision=revision,
            error=error,
        )

        return mutation_result
