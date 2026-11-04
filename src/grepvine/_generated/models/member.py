from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, TYPE_CHECKING

from attrs import define as _attrs_define

from ..types import UNSET, Unset

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
        expires_at (datetime.datetime | Unset): When the membership ends, for time-limited access granted by Grepvine
            support. Omitted for an ordinary membership.
    """

    user: User
    role: Role
    created_at: datetime.datetime
    expires_at: datetime.datetime | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        user = self.user.to_dict()

        role = self.role.value

        created_at = self.created_at.isoformat()

        expires_at: str | Unset = UNSET
        if not isinstance(self.expires_at, Unset):
            expires_at = self.expires_at.isoformat()

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "user": user,
                "role": role,
                "created_at": created_at,
            }
        )
        if expires_at is not UNSET:
            field_dict["expires_at"] = expires_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.user import User  # noqa: PLC0415

        d = dict(src_dict)
        user = User.from_dict(d.pop("user"))

        role = Role(d.pop("role"))

        created_at = datetime.datetime.fromisoformat(d.pop("created_at"))

        _expires_at = d.pop("expires_at", UNSET)
        expires_at: datetime.datetime | Unset
        if isinstance(_expires_at, Unset):
            expires_at = UNSET
        else:
            expires_at = datetime.datetime.fromisoformat(_expires_at)

        member = cls(
            user=user,
            role=role,
            created_at=created_at,
            expires_at=expires_at,
        )

        return member
