from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define


from ..models.signup_mode import SignupMode


T = TypeVar("T", bound="AuthOptions")


@_attrs_define
class AuthOptions:
    """
    Attributes:
        signup (SignupMode): How accounts are created. `open` lets anyone register; `invite` registers only with an
            invitation.
    """

    signup: SignupMode

    def to_dict(self) -> dict[str, Any]:
        signup = self.signup.value

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "signup": signup,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        signup = SignupMode(d.pop("signup"))

        auth_options = cls(
            signup=signup,
        )

        return auth_options
