from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, TYPE_CHECKING

from attrs import define as _attrs_define


if TYPE_CHECKING:
    from ..models.delete_object_record import DeleteObjectRecord


T = TypeVar("T", bound="DeleteObjectsRequest")


@_attrs_define
class DeleteObjectsRequest:
    """
    Attributes:
        objects (list[DeleteObjectRecord]):
    """

    objects: list[DeleteObjectRecord]

    def to_dict(self) -> dict[str, Any]:
        objects = []
        for objects_item_data in self.objects:
            objects_item = objects_item_data.to_dict()
            objects.append(objects_item)

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "objects": objects,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.delete_object_record import DeleteObjectRecord  # noqa: PLC0415

        d = dict(src_dict)
        objects = []
        _objects = d.pop("objects")
        for objects_item_data in _objects:
            objects_item = DeleteObjectRecord.from_dict(objects_item_data)

            objects.append(objects_item)

        delete_objects_request = cls(
            objects=objects,
        )

        return delete_objects_request
