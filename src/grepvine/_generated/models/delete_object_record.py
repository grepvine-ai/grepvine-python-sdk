from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..types import UNSET, Unset


T = TypeVar("T", bound="DeleteObjectRecord")


@_attrs_define
class DeleteObjectRecord:
    """One document of a batch to delete.

    Attributes:
        key (str): The key of the document to delete.
        if_match (str): A revision. The document is deleted only if it still has this revision; otherwise its result has
            the error `precondition_failed`.
    """

    key: str
    if_match: str | None = None

    def to_dict(self) -> dict[str, Any]:
        key = self.key
        _if_match_value = UNSET if self.if_match is None else self.if_match
        if_match = _if_match_value

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "key": key,
            }
        )
        if if_match is not UNSET:
            field_dict["if_match"] = if_match

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        key = d.pop("key")

        if_match = d.pop("if_match", UNSET)

        delete_object_record = cls(
            key=key,
            if_match=(None if isinstance(if_match, Unset) else if_match),
        )

        return delete_object_record
