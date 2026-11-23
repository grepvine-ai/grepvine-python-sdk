from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field


T = TypeVar("T", bound="StorageUsage")


@_attrs_define
class StorageUsage:
    """What is stored now: the documents and their total size, as uploaded. Metadata is not counted.

    Attributes:
        documents (int): The number of documents.
        stored_bytes (int): The total size of the documents in bytes, as uploaded and as a download returns them.
    """

    documents: int
    stored_bytes: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        documents = self.documents
        stored_bytes = self.stored_bytes

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "documents": documents,
                "stored_bytes": stored_bytes,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        documents = d.pop("documents")

        stored_bytes = d.pop("stored_bytes")

        storage_usage = cls(
            documents=documents,
            stored_bytes=stored_bytes,
        )

        storage_usage.additional_properties = d
        return storage_usage

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
