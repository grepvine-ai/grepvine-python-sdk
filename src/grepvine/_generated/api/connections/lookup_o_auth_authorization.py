from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response

from ...models.error import Error
from ...models.o_auth_authorization_request import OAuthAuthorizationRequest
from ...models.pending_o_auth_authorization import PendingOAuthAuthorization


def _get_kwargs(
    *,
    body: OAuthAuthorizationRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/oauth/authorizations/lookup",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Error | PendingOAuthAuthorization:
    if response.status_code == 200:
        response_200 = PendingOAuthAuthorization.from_dict(response.json())

        return response_200

    if response.status_code == 403:
        response_403 = Error.from_dict(response.json())

        return response_403

    response_default = Error.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[Error | PendingOAuthAuthorization]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: OAuthAuthorizationRequest,
) -> Response[Error | PendingOAuthAuthorization]:
    """Read an app's sign-in request

     Returns who an app signing in through OAuth is and what it asks to do, for a signed-in session to
    show before approving it. The permissions are those the request's `scope` names that an app can be
    granted; without any, `search` and `read`. A request that cannot be approved fails with 400, and its
    app is not sent back an answer. Only a signed-in session can read one.

    Args:
        body (OAuthAuthorizationRequest): An app's OAuth sign-in request, with the parameters it
            sent to the authorization endpoint.

    Raises:
        grepvine.APIError: The service answered with an error.
        grepvine.TransportError: The request could not be delivered.

    Returns:
        Response[Error | PendingOAuthAuthorization]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    body: OAuthAuthorizationRequest,
) -> Error | PendingOAuthAuthorization | None:
    """Read an app's sign-in request

     Returns who an app signing in through OAuth is and what it asks to do, for a signed-in session to
    show before approving it. The permissions are those the request's `scope` names that an app can be
    granted; without any, `search` and `read`. A request that cannot be approved fails with 400, and its
    app is not sent back an answer. Only a signed-in session can read one.

    Args:
        body (OAuthAuthorizationRequest): An app's OAuth sign-in request, with the parameters it
            sent to the authorization endpoint.

    Raises:
        grepvine.APIError: The service answered with an error.
        grepvine.TransportError: The request could not be delivered.

    Returns:
        Error | PendingOAuthAuthorization
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: OAuthAuthorizationRequest,
) -> Response[Error | PendingOAuthAuthorization]:
    """Read an app's sign-in request

     Returns who an app signing in through OAuth is and what it asks to do, for a signed-in session to
    show before approving it. The permissions are those the request's `scope` names that an app can be
    granted; without any, `search` and `read`. A request that cannot be approved fails with 400, and its
    app is not sent back an answer. Only a signed-in session can read one.

    Args:
        body (OAuthAuthorizationRequest): An app's OAuth sign-in request, with the parameters it
            sent to the authorization endpoint.

    Raises:
        grepvine.APIError: The service answered with an error.
        grepvine.TransportError: The request could not be delivered.

    Returns:
        Response[Error | PendingOAuthAuthorization]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: OAuthAuthorizationRequest,
) -> Error | PendingOAuthAuthorization | None:
    """Read an app's sign-in request

     Returns who an app signing in through OAuth is and what it asks to do, for a signed-in session to
    show before approving it. The permissions are those the request's `scope` names that an app can be
    granted; without any, `search` and `read`. A request that cannot be approved fails with 400, and its
    app is not sent back an answer. Only a signed-in session can read one.

    Args:
        body (OAuthAuthorizationRequest): An app's OAuth sign-in request, with the parameters it
            sent to the authorization endpoint.

    Raises:
        grepvine.APIError: The service answered with an error.
        grepvine.TransportError: The request could not be delivered.

    Returns:
        Error | PendingOAuthAuthorization
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
