from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define


from typing import Literal, cast


T = TypeVar("T", bound="TaggedIntegerMetadataValue")


@_attrs_define
class TaggedIntegerMetadataValue:
    """A 64-bit integer metadata value with its type named.

    Attributes:
        type_ (Literal['integer']): The value's type: always `integer`.
        value (int): The value, a signed 64-bit integer.
    """

    type_: Literal["integer"]
    value: int

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
        type_ = cast(Literal["integer"], d.pop("type"))
        if type_ != "integer":
            raise ValueError(f"type must match const 'integer', got '{type_}'")

        value = d.pop("value")

        tagged_integer_metadata_value = cls(
            type_=type_,
            value=value,
        )

        return tagged_integer_metadata_value
