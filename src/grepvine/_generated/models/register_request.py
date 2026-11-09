from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..types import UNSET, Unset


T = TypeVar("T", bound="RegisterRequest")


@_attrs_define
class RegisterRequest:
    """A new local account.

    Attributes:
        name (str): An account or organization name. Accounts and organizations share one namespace. A name keeps the
            case it was created with, and any spelling that differs only in case refers to it; no other account or
            organization can take such a spelling.
        email (str): The account's email address, at most 320 characters. No other account can use it.
        password (str): The password, 12 to 1,024 characters.
        invitation (str): The token of the invitation link the account was invited with. Required when registration is
            by invitation.
    """

    name: str
    email: str
    password: str
    invitation: str | None = None

    def to_dict(self) -> dict[str, Any]:
        name = self.name
        email = self.email
        password = self.password
        _invitation_value = UNSET if self.invitation is None else self.invitation
        invitation = _invitation_value

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "name": name,
                "email": email,
                "password": password,
            }
        )
        if invitation is not UNSET:
            field_dict["invitation"] = invitation

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name")

        email = d.pop("email")

        password = d.pop("password")

        invitation = d.pop("invitation", UNSET)

        register_request = cls(
            name=name,
            email=email,
            password=password,
            invitation=(None if isinstance(invitation, Unset) else invitation),
        )

        return register_request
