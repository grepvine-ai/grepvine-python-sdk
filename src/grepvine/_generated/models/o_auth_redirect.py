from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define


T = TypeVar("T", bound="OAuthRedirect")


@_attrs_define
class OAuthRedirect:
    """Where to send the browser to answer the app.

    Attributes:
        redirect_to (str): The app's address, carrying the answer.
    """

    redirect_to: str

    def to_dict(self) -> dict[str, Any]:
        redirect_to = self.redirect_to

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "redirect_to": redirect_to,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        redirect_to = d.pop("redirect_to")

        o_auth_redirect = cls(
            redirect_to=redirect_to,
        )

        return o_auth_redirect
