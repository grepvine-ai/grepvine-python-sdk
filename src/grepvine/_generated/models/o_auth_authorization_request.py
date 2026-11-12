from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..types import UNSET, Unset


T = TypeVar("T", bound="OAuthAuthorizationRequest")


@_attrs_define
class OAuthAuthorizationRequest:
    """An app's OAuth sign-in request, with the parameters it sent to the authorization endpoint.

    Attributes:
        response_type (str): Must be `code`.
        client_id (str): The app's client ID: the HTTPS address of its client metadata document.
        redirect_uri (str): Where the app receives the answer; one of the addresses its metadata document lists.
        code_challenge (str): The PKCE code challenge, 43 to 128 characters.
        code_challenge_method (str): Must be `S256`.
        resource (str): The MCP server the app signs in to.
        state (str): A value the app sent, returned to it unchanged, at most 1,024 characters.
        scope (str): The space-separated scopes the app asked for.
    """

    response_type: str
    client_id: str
    redirect_uri: str
    code_challenge: str
    code_challenge_method: str
    resource: str
    state: str | None = None
    scope: str | None = None

    def to_dict(self) -> dict[str, Any]:
        response_type = self.response_type
        client_id = self.client_id
        redirect_uri = self.redirect_uri
        code_challenge = self.code_challenge
        code_challenge_method = self.code_challenge_method
        resource = self.resource
        _state_value = UNSET if self.state is None else self.state
        state = _state_value
        _scope_value = UNSET if self.scope is None else self.scope
        scope = _scope_value

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "response_type": response_type,
                "client_id": client_id,
                "redirect_uri": redirect_uri,
                "code_challenge": code_challenge,
                "code_challenge_method": code_challenge_method,
                "resource": resource,
            }
        )
        if state is not UNSET:
            field_dict["state"] = state
        if scope is not UNSET:
            field_dict["scope"] = scope

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        response_type = d.pop("response_type")

        client_id = d.pop("client_id")

        redirect_uri = d.pop("redirect_uri")

        code_challenge = d.pop("code_challenge")

        code_challenge_method = d.pop("code_challenge_method")

        resource = d.pop("resource")

        state = d.pop("state", UNSET)

        scope = d.pop("scope", UNSET)

        o_auth_authorization_request = cls(
            response_type=response_type,
            client_id=client_id,
            redirect_uri=redirect_uri,
            code_challenge=code_challenge,
            code_challenge_method=code_challenge_method,
            resource=resource,
            state=(None if isinstance(state, Unset) else state),
            scope=(None if isinstance(scope, Unset) else scope),
        )

        return o_auth_authorization_request
