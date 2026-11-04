from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, TYPE_CHECKING

from attrs import define as _attrs_define
from attrs import field as _attrs_field


from typing import cast

if TYPE_CHECKING:
    from ..models.tagged_boolean_metadata_value import TaggedBooleanMetadataValue
    from ..models.tagged_integer_metadata_value import TaggedIntegerMetadataValue
    from ..models.tagged_number_metadata_value import TaggedNumberMetadataValue
    from ..models.tagged_string_metadata_value import TaggedStringMetadataValue
    from ..models.tagged_timestamp_metadata_value import TaggedTimestampMetadataValue


T = TypeVar("T", bound="Metadata")


@_attrs_define
class Metadata:
    additional_properties: dict[
        str,
        bool
        | int
        | str
        | TaggedBooleanMetadataValue
        | TaggedIntegerMetadataValue
        | TaggedNumberMetadataValue
        | TaggedStringMetadataValue
        | TaggedTimestampMetadataValue,
    ] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.tagged_boolean_metadata_value import TaggedBooleanMetadataValue  # noqa: PLC0415
        from ..models.tagged_integer_metadata_value import TaggedIntegerMetadataValue  # noqa: PLC0415
        from ..models.tagged_number_metadata_value import TaggedNumberMetadataValue  # noqa: PLC0415
        from ..models.tagged_string_metadata_value import TaggedStringMetadataValue  # noqa: PLC0415
        from ..models.tagged_timestamp_metadata_value import TaggedTimestampMetadataValue  # noqa: PLC0415

        field_dict: dict[str, Any] = {}
        for prop_name, prop in self.additional_properties.items():
            if isinstance(prop, TaggedStringMetadataValue):
                field_dict[prop_name] = prop.to_dict()
            elif isinstance(prop, TaggedIntegerMetadataValue):
                field_dict[prop_name] = prop.to_dict()
            elif isinstance(prop, TaggedNumberMetadataValue):
                field_dict[prop_name] = prop.to_dict()
            elif isinstance(prop, TaggedBooleanMetadataValue):
                field_dict[prop_name] = prop.to_dict()
            elif isinstance(prop, TaggedTimestampMetadataValue):
                field_dict[prop_name] = prop.to_dict()
            else:
                field_dict[prop_name] = prop

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.tagged_boolean_metadata_value import TaggedBooleanMetadataValue  # noqa: PLC0415
        from ..models.tagged_integer_metadata_value import TaggedIntegerMetadataValue  # noqa: PLC0415
        from ..models.tagged_number_metadata_value import TaggedNumberMetadataValue  # noqa: PLC0415
        from ..models.tagged_string_metadata_value import TaggedStringMetadataValue  # noqa: PLC0415
        from ..models.tagged_timestamp_metadata_value import TaggedTimestampMetadataValue  # noqa: PLC0415

        d = dict(src_dict)
        metadata = cls()

        additional_properties = {}
        for prop_name, prop_dict in d.items():

            def _parse_additional_property(
                data: object,
            ) -> (
                bool
                | int
                | str
                | TaggedBooleanMetadataValue
                | TaggedIntegerMetadataValue
                | TaggedNumberMetadataValue
                | TaggedStringMetadataValue
                | TaggedTimestampMetadataValue
            ):
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    componentsschemas_tagged_metadata_value_type_0 = (
                        TaggedStringMetadataValue.from_dict(data)
                    )

                    return componentsschemas_tagged_metadata_value_type_0
                except (TypeError, ValueError, AttributeError, KeyError):
                    pass
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    componentsschemas_tagged_metadata_value_type_1 = (
                        TaggedIntegerMetadataValue.from_dict(data)
                    )

                    return componentsschemas_tagged_metadata_value_type_1
                except (TypeError, ValueError, AttributeError, KeyError):
                    pass
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    componentsschemas_tagged_metadata_value_type_2 = (
                        TaggedNumberMetadataValue.from_dict(data)
                    )

                    return componentsschemas_tagged_metadata_value_type_2
                except (TypeError, ValueError, AttributeError, KeyError):
                    pass
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    componentsschemas_tagged_metadata_value_type_3 = (
                        TaggedBooleanMetadataValue.from_dict(data)
                    )

                    return componentsschemas_tagged_metadata_value_type_3
                except (TypeError, ValueError, AttributeError, KeyError):
                    pass
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    componentsschemas_tagged_metadata_value_type_4 = (
                        TaggedTimestampMetadataValue.from_dict(data)
                    )

                    return componentsschemas_tagged_metadata_value_type_4
                except (TypeError, ValueError, AttributeError, KeyError):
                    pass
                return cast(
                    bool
                    | int
                    | str
                    | TaggedBooleanMetadataValue
                    | TaggedIntegerMetadataValue
                    | TaggedNumberMetadataValue
                    | TaggedStringMetadataValue
                    | TaggedTimestampMetadataValue,
                    data,
                )

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
        bool
        | int
        | str
        | TaggedBooleanMetadataValue
        | TaggedIntegerMetadataValue
        | TaggedNumberMetadataValue
        | TaggedStringMetadataValue
        | TaggedTimestampMetadataValue
    ):
        return self.additional_properties[key]

    def __setitem__(
        self,
        key: str,
        value: bool
        | int
        | str
        | TaggedBooleanMetadataValue
        | TaggedIntegerMetadataValue
        | TaggedNumberMetadataValue
        | TaggedStringMetadataValue
        | TaggedTimestampMetadataValue,
    ) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
