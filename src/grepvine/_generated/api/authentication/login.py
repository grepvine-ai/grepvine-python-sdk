from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response

from ...models.error import Error
from ...models.login_request import LoginRequest
from ...models.user import User


def _get_kwargs(
    *,
    body: LoginRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/auth/login",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Error | User:
    if response.status_code == 200:
        response_200 = User.from_dict(response.json())

        return response_200

    if response.status_code == 401:
        response_401 = Error.from_dict(response.json())

        return response_401

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
    body: LoginRequest,
) -> Response[Error | User]:
    """Create a user session

    Args:
        body (LoginRequest):

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
    body: LoginRequest,
) -> Error | User | None:
    """Create a user session

    Args:
        body (LoginRequest):

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
    body: LoginRequest,
) -> Response[Error | User]:
    """Create a user session

    Args:
        body (LoginRequest):

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
    body: LoginRequest,
) -> Error | User | None:
    """Create a user session

    Args:
        body (LoginRequest):

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
