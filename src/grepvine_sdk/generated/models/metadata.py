from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, TYPE_CHECKING

from attrs import define as _attrs_define
from attrs import field as _attrs_field


if TYPE_CHECKING:
    from ..models.boolean_metadata_value import BooleanMetadataValue
    from ..models.integer_metadata_value import IntegerMetadataValue
    from ..models.number_metadata_value import NumberMetadataValue
    from ..models.string_metadata_value import StringMetadataValue
    from ..models.timestamp_metadata_value import TimestampMetadataValue


T = TypeVar("T", bound="Metadata")


@_attrs_define
class Metadata:
    additional_properties: dict[
        str,
        BooleanMetadataValue
        | IntegerMetadataValue
        | NumberMetadataValue
        | StringMetadataValue
        | TimestampMetadataValue,
    ] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.boolean_metadata_value import BooleanMetadataValue  # noqa: PLC0415
        from ..models.integer_metadata_value import IntegerMetadataValue  # noqa: PLC0415
        from ..models.number_metadata_value import NumberMetadataValue  # noqa: PLC0415
        from ..models.string_metadata_value import StringMetadataValue  # noqa: PLC0415

        field_dict: dict[str, Any] = {}
        for prop_name, prop in self.additional_properties.items():
            if isinstance(prop, StringMetadataValue):
                field_dict[prop_name] = prop.to_dict()
            elif isinstance(prop, IntegerMetadataValue):
                field_dict[prop_name] = prop.to_dict()
            elif isinstance(prop, NumberMetadataValue):
                field_dict[prop_name] = prop.to_dict()
            elif isinstance(prop, BooleanMetadataValue):
                field_dict[prop_name] = prop.to_dict()
            else:
                field_dict[prop_name] = prop.to_dict()

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.boolean_metadata_value import BooleanMetadataValue  # noqa: PLC0415
        from ..models.integer_metadata_value import IntegerMetadataValue  # noqa: PLC0415
        from ..models.number_metadata_value import NumberMetadataValue  # noqa: PLC0415
        from ..models.string_metadata_value import StringMetadataValue  # noqa: PLC0415
        from ..models.timestamp_metadata_value import TimestampMetadataValue  # noqa: PLC0415

        d = dict(src_dict)
        metadata = cls()

        additional_properties = {}
        for prop_name, prop_dict in d.items():

            def _parse_additional_property(
                data: object,
            ) -> (
                BooleanMetadataValue
                | IntegerMetadataValue
                | NumberMetadataValue
                | StringMetadataValue
                | TimestampMetadataValue
            ):
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    componentsschemas_metadata_value_type_0 = StringMetadataValue.from_dict(data)

                    return componentsschemas_metadata_value_type_0
                except (TypeError, ValueError, AttributeError, KeyError):
                    pass
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    componentsschemas_metadata_value_type_1 = IntegerMetadataValue.from_dict(data)

                    return componentsschemas_metadata_value_type_1
                except (TypeError, ValueError, AttributeError, KeyError):
                    pass
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    componentsschemas_metadata_value_type_2 = NumberMetadataValue.from_dict(data)

                    return componentsschemas_metadata_value_type_2
                except (TypeError, ValueError, AttributeError, KeyError):
                    pass
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    componentsschemas_metadata_value_type_3 = BooleanMetadataValue.from_dict(data)

                    return componentsschemas_metadata_value_type_3
                except (TypeError, ValueError, AttributeError, KeyError):
                    pass
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_metadata_value_type_4 = TimestampMetadataValue.from_dict(data)

                return componentsschemas_metadata_value_type_4

            additional_property = _parse_additional_property(prop_dict)

            additional_properties[prop_name] = additional_property

        metadata.additional_properties = additional_properties
        return metadata

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(
        self, key: str
    ) -> (
        BooleanMetadataValue
        | IntegerMetadataValue
        | NumberMetadataValue
        | StringMetadataValue
        | TimestampMetadataValue
    ):
        return self.additional_properties[key]

    def __setitem__(
        self,
        key: str,
        value: BooleanMetadataValue
        | IntegerMetadataValue
        | NumberMetadataValue
        | StringMetadataValue
        | TimestampMetadataValue,
    ) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
