from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, TYPE_CHECKING

from attrs import define as _attrs_define
from attrs import field as _attrs_field


if TYPE_CHECKING:
    from ..models.error_detail_metadata import ErrorDetailMetadata


T = TypeVar("T", bound="ErrorDetail")


@_attrs_define
class ErrorDetail:
    """One piece of information about an error. `type` names what it is and which `metadata` keys it carries;
    clients ignore types they do not know. `missing_permission`: the API key lacks the permission
    `metadata.permission` names. `agent_missing_permission`: the agent lacks the permission
    `metadata.permission` names; one of its managers can grant it.

        Attributes:
            type_ (str): What the detail is, such as `missing_permission`.
            metadata (ErrorDetailMetadata): The detail's values, by key.
    """

    type_: str
    metadata: ErrorDetailMetadata
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        type_ = self.type_
        metadata = self.metadata.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
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

        error_detail.additional_properties = d
        return error_detail

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
