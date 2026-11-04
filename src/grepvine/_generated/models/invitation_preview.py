from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..types import UNSET, Unset

from ..models.invitation_role import InvitationRole
import datetime


T = TypeVar("T", bound="InvitationPreview")


@_attrs_define
class InvitationPreview:
    """
    Attributes:
        email (str): The address the invitation was sent to, to prefill the registration form.
        expires_at (datetime.datetime):
        organization (str | Unset): An account or organization name. Accounts and organizations share one namespace. A
            name keeps the case it was created with, and any spelling that differs only in case refers to it; no other
            account or organization can take such a spelling.
        role (InvitationRole | Unset):
    """

    email: str
    expires_at: datetime.datetime
    organization: str | Unset = UNSET
    role: InvitationRole | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        email = self.email

        expires_at = self.expires_at.isoformat()

        organization = self.organization

        role: str | Unset = UNSET
        if not isinstance(self.role, Unset):
            role = self.role.value

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "email": email,
                "expires_at": expires_at,
            }
        )
        if organization is not UNSET:
            field_dict["organization"] = organization
        if role is not UNSET:
            field_dict["role"] = role

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        email = d.pop("email")

        expires_at = datetime.datetime.fromisoformat(d.pop("expires_at"))

        organization = d.pop("organization", UNSET)

        _role = d.pop("role", UNSET)
        role: InvitationRole | Unset
        if isinstance(_role, Unset):
            role = UNSET
        else:
            role = InvitationRole(_role)

        invitation_preview = cls(
            email=email,
            expires_at=expires_at,
            organization=organization,
            role=role,
        )

        return invitation_preview
