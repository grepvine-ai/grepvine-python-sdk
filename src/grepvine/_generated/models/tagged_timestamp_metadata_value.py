from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define


from typing import cast
from typing import Literal
import datetime


T = TypeVar("T", bound="TaggedTimestampMetadataValue")


@_attrs_define
class TaggedTimestampMetadataValue:
    """A timestamp metadata value with its type named.

    Attributes:
        type_ (Literal['timestamp']): The value's type: always `timestamp`.
        value (datetime.datetime): The value, an RFC 3339 date and time.
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

        tagged_timestamp_metadata_value = cls(
            type_=type_,
            value=value,
        )

        return tagged_timestamp_metadata_value
