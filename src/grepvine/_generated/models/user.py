from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..models.staff_role import StaffRole
from uuid import UUID
import datetime


T = TypeVar("T", bound="User")


@_attrs_define
class User:
    """A user account.

    Attributes:
        id (UUID): The account's unique ID.
        name (str): A name: of an account, an organization or an agent. Accounts and organizations share one namespace;
            an agent's name is unique within its organization. A name keeps the case it was created with, and any spelling
            that differs only in case refers to it; nothing else in the same namespace can take such a spelling.
        email (str): The account's email address.
        created_at (datetime.datetime): When the account was created.
        staff_role (StaffRole): The account's role on the Grepvine team, when it has one. Omitted for every other
            account.
    """

    id: UUID
    name: str
    email: str
    created_at: datetime.datetime
    staff_role: StaffRole | None = None
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)
        name = self.name
        email = self.email
        created_at = self.created_at.isoformat()
        _staff_role_value = UNSET if self.staff_role is None else self.staff_role
        staff_role: str | Unset = UNSET
        if not isinstance(_staff_role_value, Unset):
            staff_role = _staff_role_value.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "email": email,
                "created_at": created_at,
            }
        )
        if staff_role is not UNSET:
            field_dict["staff_role"] = staff_role

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = UUID(d.pop("id"))

        name = d.pop("name")

        email = d.pop("email")

        created_at = datetime.datetime.fromisoformat(d.pop("created_at"))

        _staff_role = d.pop("staff_role", UNSET)
        staff_role: StaffRole | Unset
        if isinstance(_staff_role, Unset):
            staff_role = UNSET
        else:
            staff_role = StaffRole(_staff_role)

        user = cls(
            id=id,
            name=name,
            email=email,
            created_at=created_at,
            staff_role=(None if isinstance(staff_role, Unset) else staff_role),
        )

        user.additional_properties = d
        return user

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
