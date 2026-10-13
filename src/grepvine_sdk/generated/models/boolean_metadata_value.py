from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define


from typing import Literal, cast


T = TypeVar("T", bound="BooleanMetadataValue")


@_attrs_define
class BooleanMetadataValue:
    """
    Attributes:
        type_ (Literal['boolean']):
        value (bool):
    """

    type_: Literal["boolean"]
    value: bool

    def to_dict(self) -> dict[str, Any]:
        type_ = self.type_

        value = self.value

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "type": type_,
                "value": value,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        type_ = cast(Literal["boolean"], d.pop("type"))
        if type_ != "boolean":
            raise ValueError(f"type must match const 'boolean', got '{type_}'")

        value = d.pop("value")

        boolean_metadata_value = cls(
            type_=type_,
            value=value,
        )

        return boolean_metadata_value
