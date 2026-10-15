from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, TYPE_CHECKING

from attrs import define as _attrs_define


from ..models.role import Role
import datetime

if TYPE_CHECKING:
    from ..models.user import User


T = TypeVar("T", bound="Member")


@_attrs_define
class Member:
    """
    Attributes:
        user (User):
        role (Role):
        created_at (datetime.datetime):
    """

    user: User
    role: Role
    created_at: datetime.datetime

    def to_dict(self) -> dict[str, Any]:
        user = self.user.to_dict()

        role = self.role.value

        created_at = self.created_at.isoformat()

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "user": user,
                "role": role,
                "created_at": created_at,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.user import User  # noqa: PLC0415

        d = dict(src_dict)
        user = User.from_dict(d.pop("user"))

        role = Role(d.pop("role"))

        created_at = datetime.datetime.fromisoformat(d.pop("created_at"))

        member = cls(
            user=user,
            role=role,
            created_at=created_at,
        )

        return member
