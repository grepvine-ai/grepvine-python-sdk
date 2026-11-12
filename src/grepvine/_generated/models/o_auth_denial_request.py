from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, TYPE_CHECKING

from attrs import define as _attrs_define


if TYPE_CHECKING:
    from ..models.o_auth_authorization_request import OAuthAuthorizationRequest


T = TypeVar("T", bound="OAuthDenialRequest")


@_attrs_define
class OAuthDenialRequest:
    """The sign-in request to deny.

    Attributes:
        request (OAuthAuthorizationRequest): An app's OAuth sign-in request, with the parameters it sent to the
            authorization endpoint.
    """

    request: OAuthAuthorizationRequest

    def to_dict(self) -> dict[str, Any]:
        request = self.request.to_dict()

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "request": request,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.o_auth_authorization_request import OAuthAuthorizationRequest  # noqa: PLC0415

        d = dict(src_dict)
        request = OAuthAuthorizationRequest.from_dict(d.pop("request"))

        o_auth_denial_request = cls(
            request=request,
        )

        return o_auth_denial_request
