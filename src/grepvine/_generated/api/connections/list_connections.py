from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response

from ...models.connection_page import ConnectionPage
from ...models.error import Error


def _get_kwargs() -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/connections",
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ConnectionPage | Error:
    if response.status_code == 200:
        response_200 = ConnectionPage.from_dict(response.json())

        return response_200

    if response.status_code == 403:
        response_403 = Error.from_dict(response.json())

        return response_403

    response_default = Error.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[ConnectionPage | Error]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
) -> Response[ConnectionPage | Error]:
    """List connections

     Lists the apps you have connected that are still in use: revoked and ended connections are left out.
    Newest first. Only a signed-in session can list them.

    Raises:
        grepvine.APIError: The service answered with an error.
        grepvine.TransportError: The request could not be delivered.

    Returns:
        Response[ConnectionPage | Error]
    """

    kwargs = _get_kwargs()

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
) -> ConnectionPage | Error | None:
    """List connections

     Lists the apps you have connected that are still in use: revoked and ended connections are left out.
    Newest first. Only a signed-in session can list them.

    Raises:
        grepvine.APIError: The service answered with an error.
        grepvine.TransportError: The request could not be delivered.

    Returns:
        ConnectionPage | Error
    """

    return sync_detailed(
        client=client,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
) -> Response[ConnectionPage | Error]:
    """List connections

     Lists the apps you have connected that are still in use: revoked and ended connections are left out.
    Newest first. Only a signed-in session can list them.

    Raises:
        grepvine.APIError: The service answered with an error.
        grepvine.TransportError: The request could not be delivered.

    Returns:
        Response[ConnectionPage | Error]
    """

    kwargs = _get_kwargs()

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
) -> ConnectionPage | Error | None:
    """List connections

     Lists the apps you have connected that are still in use: revoked and ended connections are left out.
    Newest first. Only a signed-in session can list them.

    Raises:
        grepvine.APIError: The service answered with an error.
        grepvine.TransportError: The request could not be delivered.

    Returns:
        ConnectionPage | Error
    """

    return (
        await asyncio_detailed(
            client=client,
        )
    ).parsed
