from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, TYPE_CHECKING

from attrs import define as _attrs_define


if TYPE_CHECKING:
    from ..models.connection_scope import ConnectionScope
    from ..models.o_auth_authorization_request import OAuthAuthorizationRequest


T = TypeVar("T", bound="OAuthApprovalRequest")


@_attrs_define
class OAuthApprovalRequest:
    """The sign-in request to approve and the scope to grant it.

    Attributes:
        request (OAuthAuthorizationRequest): An app's OAuth sign-in request, with the parameters it sent to the
            authorization endpoint.
        scope (ConnectionScope): What a connection reaches and may do. A field left out sets no limit.
    """

    request: OAuthAuthorizationRequest
    scope: ConnectionScope

    def to_dict(self) -> dict[str, Any]:
        request = self.request.to_dict()
        scope = self.scope.to_dict()

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "request": request,
                "scope": scope,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.connection_scope import ConnectionScope  # noqa: PLC0415
        from ..models.o_auth_authorization_request import OAuthAuthorizationRequest  # noqa: PLC0415

        d = dict(src_dict)
        request = OAuthAuthorizationRequest.from_dict(d.pop("request"))

        scope = ConnectionScope.from_dict(d.pop("scope"))

        o_auth_approval_request = cls(
            request=request,
            scope=scope,
        )

        return o_auth_approval_request
