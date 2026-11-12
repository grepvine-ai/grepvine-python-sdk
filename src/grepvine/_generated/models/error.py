from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, TYPE_CHECKING

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset


if TYPE_CHECKING:
    from ..models.error_detail import ErrorDetail


T = TypeVar("T", bound="Error")


@_attrs_define
class Error:
    """A failed request. `code` says what went wrong and is stable; branch on it, not on the message.

    Attributes:
        code (str): A stable, machine-readable code, such as `invalid_pattern`, `not_found` or `write_backlog`.
        reason (str): The broad category of the error, such as `validation`, `authentication`, `state` or `capacity`.
        error (str): A message for people that says what went wrong and what to do about it.
        details (list[ErrorDetail]): Structured information about the error. Omitted when there is none.
    """

    code: str
    reason: str
    error: str
    details: list[ErrorDetail] = _attrs_field(factory=list)

    def to_dict(self) -> dict[str, Any]:
        code = self.code
        reason = self.reason
        error = self.error
        _details_value = UNSET if self.details is None else self.details
        details: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(_details_value, Unset):
            details = []
            for details_item_data in _details_value:
                details_item = details_item_data.to_dict()
                details.append(details_item)

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "code": code,
                "reason": reason,
                "error": error,
            }
        )
        if details is not UNSET:
            field_dict["details"] = details

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.error_detail import ErrorDetail  # noqa: PLC0415

        d = dict(src_dict)
        code = d.pop("code")

        reason = d.pop("reason")

        error = d.pop("error")

        _details = d.pop("details", UNSET)
        details: list[ErrorDetail] | Unset = UNSET
        if _details is not UNSET:
            details = []
            for details_item_data in _details:
                details_item = ErrorDetail.from_dict(details_item_data)

                details.append(details_item)

        error = cls(
            code=code,
            reason=reason,
            error=error,
            details=([] if isinstance(details, Unset) else details),
        )

        return error
