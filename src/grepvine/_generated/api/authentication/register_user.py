from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response

from ...models.error import Error
from ...models.register_request import RegisterRequest
from ...models.user import User


def _get_kwargs(
    *,
    body: RegisterRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/auth/register",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Error | User:
    if response.status_code == 201:
        response_201 = User.from_dict(response.json())

        return response_201

    if response.status_code == 409:
        response_409 = Error.from_dict(response.json())

        return response_409

    response_default = Error.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[Error | User]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: RegisterRequest,
) -> Response[Error | User]:
    """Register a local user

     A 409 has code `username_taken` when an account or an organization already holds the username, and
    code `email_taken` when an account already uses the email address.

    Args:
        body (RegisterRequest):

    Raises:
        grepvine.APIError: The service answered with an error.
        grepvine.TransportError: The request could not be delivered.

    Returns:
        Response[Error | User]
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
    body: RegisterRequest,
) -> Error | User | None:
    """Register a local user

     A 409 has code `username_taken` when an account or an organization already holds the username, and
    code `email_taken` when an account already uses the email address.

    Args:
        body (RegisterRequest):

    Raises:
        grepvine.APIError: The service answered with an error.
        grepvine.TransportError: The request could not be delivered.

    Returns:
        Error | User
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: RegisterRequest,
) -> Response[Error | User]:
    """Register a local user

     A 409 has code `username_taken` when an account or an organization already holds the username, and
    code `email_taken` when an account already uses the email address.

    Args:
        body (RegisterRequest):

    Raises:
        grepvine.APIError: The service answered with an error.
        grepvine.TransportError: The request could not be delivered.

    Returns:
        Response[Error | User]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: RegisterRequest,
) -> Error | User | None:
    """Register a local user

     A 409 has code `username_taken` when an account or an organization already holds the username, and
    code `email_taken` when an account already uses the email address.

    Args:
        body (RegisterRequest):

    Raises:
        grepvine.APIError: The service answered with an error.
        grepvine.TransportError: The request could not be delivered.

    Returns:
        Error | User
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
