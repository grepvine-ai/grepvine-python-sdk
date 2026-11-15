from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, TYPE_CHECKING

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset


if TYPE_CHECKING:
    from ..models.error import Error


T = TypeVar("T", bound="MutationResult")


@_attrs_define
class MutationResult:
    """The outcome of one document. A stored or deleted document has a revision; a document a batch did not change has an
    error instead.

        Attributes:
            key (str): The document's key.
            revision (str): The document's revision after the write. Omitted when the document was not changed.
            error (Error): A failed request. `code` says what went wrong and is stable; branch on it, not on the message.
    """

    key: str
    revision: str | None = None
    error: Error | None = None
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        key = self.key
        _revision_value = UNSET if self.revision is None else self.revision
        revision = _revision_value
        _error_value = UNSET if self.error is None else self.error
        error: dict[str, Any] | Unset = UNSET
        if not isinstance(_error_value, Unset):
            error = _error_value.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "key": key,
            }
        )
        if revision is not UNSET:
            field_dict["revision"] = revision
        if error is not UNSET:
            field_dict["error"] = error

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.error import Error  # noqa: PLC0415

        d = dict(src_dict)
        key = d.pop("key")

        revision = d.pop("revision", UNSET)

        _error = d.pop("error", UNSET)
        error: Error | Unset
        if isinstance(_error, Unset):
            error = UNSET
        else:
            error = Error.from_dict(_error)

        mutation_result = cls(
            key=key,
            revision=(None if isinstance(revision, Unset) else revision),
            error=(None if isinstance(error, Unset) else error),
        )

        mutation_result.additional_properties = d
        return mutation_result

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
