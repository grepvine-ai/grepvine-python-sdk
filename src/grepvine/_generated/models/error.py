from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define


T = TypeVar("T", bound="Error")


@_attrs_define
class Error:
    """
    Attributes:
        code (str):
        reason (str):
        error (str):
    """

    code: str
    reason: str
    error: str

    def to_dict(self) -> dict[str, Any]:
        code = self.code

        reason = self.reason

        error = self.error

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "code": code,
                "reason": reason,
                "error": error,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        code = d.pop("code")

        reason = d.pop("reason")

        error = d.pop("error")

        error = cls(
            code=code,
            reason=reason,
            error=error,
        )

        return error
