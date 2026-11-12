from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response

from ...models.error import Error
from ...models.o_auth_denial_request import OAuthDenialRequest
from ...models.o_auth_redirect import OAuthRedirect


def _get_kwargs(
    *,
    body: OAuthDenialRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/oauth/authorizations/deny",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Error | OAuthRedirect:
    if response.status_code == 200:
        response_200 = OAuthRedirect.from_dict(response.json())

        return response_200

    if response.status_code == 403:
        response_403 = Error.from_dict(response.json())

        return response_403

    response_default = Error.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[Error | OAuthRedirect]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: OAuthDenialRequest,
) -> Response[Error | OAuthRedirect]:
    """Deny an app's sign-in request

     Denies an app's sign-in request and returns the address to send the browser to, which tells the app
    it was refused with `access_denied`. Only a signed-in session can deny.

    Args:
        body (OAuthDenialRequest): The sign-in request to deny.

    Raises:
        grepvine.APIError: The service answered with an error.
        grepvine.TransportError: The request could not be delivered.

    Returns:
        Response[Error | OAuthRedirect]
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
    body: OAuthDenialRequest,
) -> Error | OAuthRedirect | None:
    """Deny an app's sign-in request

     Denies an app's sign-in request and returns the address to send the browser to, which tells the app
    it was refused with `access_denied`. Only a signed-in session can deny.

    Args:
        body (OAuthDenialRequest): The sign-in request to deny.

    Raises:
        grepvine.APIError: The service answered with an error.
        grepvine.TransportError: The request could not be delivered.

    Returns:
        Error | OAuthRedirect
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: OAuthDenialRequest,
) -> Response[Error | OAuthRedirect]:
    """Deny an app's sign-in request

     Denies an app's sign-in request and returns the address to send the browser to, which tells the app
    it was refused with `access_denied`. Only a signed-in session can deny.

    Args:
        body (OAuthDenialRequest): The sign-in request to deny.

    Raises:
        grepvine.APIError: The service answered with an error.
        grepvine.TransportError: The request could not be delivered.

    Returns:
        Response[Error | OAuthRedirect]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: OAuthDenialRequest,
) -> Error | OAuthRedirect | None:
    """Deny an app's sign-in request

     Denies an app's sign-in request and returns the address to send the browser to, which tells the app
    it was refused with `access_denied`. Only a signed-in session can deny.

    Args:
        body (OAuthDenialRequest): The sign-in request to deny.

    Raises:
        grepvine.APIError: The service answered with an error.
        grepvine.TransportError: The request could not be delivered.

    Returns:
        Error | OAuthRedirect
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
