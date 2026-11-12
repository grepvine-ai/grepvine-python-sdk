from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, TYPE_CHECKING

from attrs import define as _attrs_define

from ..types import UNSET, Unset


if TYPE_CHECKING:
    from ..models.key_scope import KeyScope


T = TypeVar("T", bound="DeviceApprovalRequest")


@_attrs_define
class DeviceApprovalRequest:
    """The device authorization to approve, and optionally the scope to grant.

    Attributes:
        user_code (str): The code the device shows. Hyphens, surrounding spaces and case are ignored.
        scope (KeyScope): What a key reaches and may do. A field left out sets no limit.
    """

    user_code: str
    scope: KeyScope | None = None

    def to_dict(self) -> dict[str, Any]:
        user_code = self.user_code
        _scope_value = UNSET if self.scope is None else self.scope
        scope: dict[str, Any] | Unset = UNSET
        if not isinstance(_scope_value, Unset):
            scope = _scope_value.to_dict()

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "user_code": user_code,
            }
        )
        if scope is not UNSET:
            field_dict["scope"] = scope

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.key_scope import KeyScope  # noqa: PLC0415

        d = dict(src_dict)
        user_code = d.pop("user_code")

        _scope = d.pop("scope", UNSET)
        scope: KeyScope | Unset
        if isinstance(_scope, Unset):
            scope = UNSET
        else:
            scope = KeyScope.from_dict(_scope)

        device_approval_request = cls(
            user_code=user_code,
            scope=(None if isinstance(scope, Unset) else scope),
        )

        return device_approval_request
