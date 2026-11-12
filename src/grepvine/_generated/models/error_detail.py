from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, TYPE_CHECKING

from attrs import define as _attrs_define


if TYPE_CHECKING:
    from ..models.error_detail_metadata import ErrorDetailMetadata


T = TypeVar("T", bound="ErrorDetail")


@_attrs_define
class ErrorDetail:
    """One piece of information about an error. `type` names what it is and which `metadata` keys it carries;
    clients ignore types they do not know. `missing_permission`: the API key lacks the permission
    `metadata.permission` names.

        Attributes:
            type_ (str): What the detail is, such as `missing_permission`.
            metadata (ErrorDetailMetadata): The detail's values, by key.
    """

    type_: str
    metadata: ErrorDetailMetadata

    def to_dict(self) -> dict[str, Any]:
        type_ = self.type_
        metadata = self.metadata.to_dict()

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "type": type_,
                "metadata": metadata,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.error_detail_metadata import ErrorDetailMetadata  # noqa: PLC0415

        d = dict(src_dict)
        type_ = d.pop("type")

        metadata = ErrorDetailMetadata.from_dict(d.pop("metadata"))

        error_detail = cls(
            type_=type_,
            metadata=metadata,
        )

        return error_detail
