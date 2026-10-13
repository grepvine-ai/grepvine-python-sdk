from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define


from typing import cast
from typing import Literal
import datetime


T = TypeVar("T", bound="TimestampMetadataValue")


@_attrs_define
class TimestampMetadataValue:
    """
    Attributes:
        type_ (Literal['timestamp']):
        value (datetime.datetime):
    """

    type_: Literal["timestamp"]
    value: datetime.datetime

    def to_dict(self) -> dict[str, Any]:
        type_ = self.type_

        value = self.value.isoformat()

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
        type_ = cast(Literal["timestamp"], d.pop("type"))
        if type_ != "timestamp":
            raise ValueError(f"type must match const 'timestamp', got '{type_}'")

        value = datetime.datetime.fromisoformat(d.pop("value"))

        timestamp_metadata_value = cls(
            type_=type_,
            value=value,
        )

        return timestamp_metadata_value
