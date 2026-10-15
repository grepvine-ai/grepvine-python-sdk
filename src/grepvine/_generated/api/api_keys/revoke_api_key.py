from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response

from ...models.error import Error
from uuid import UUID


def _get_kwargs(
    api_key_id: UUID,
) -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "delete",
        "url": "/api-keys/{api_key_id}".format(
            api_key_id=quote(str(api_key_id), safe=""),
        ),
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Any | Error:
    if response.status_code == 204:
        response_204 = cast(Any, None)
        return response_204

    if response.status_code == 404:
        response_404 = Error.from_dict(response.json())

        return response_404

    response_default = Error.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[Any | Error]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    api_key_id: UUID,
    *,
    client: AuthenticatedClient | Client,
) -> Response[Any | Error]:
    """Revoke an API key

    Args:
        api_key_id (UUID):

    Raises:
        grepvine.APIError: The service answered with an error.
        grepvine.TransportError: The request could not be delivered.

    Returns:
        Response[Any | Error]
    """

    kwargs = _get_kwargs(
        api_key_id=api_key_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    api_key_id: UUID,
    *,
    client: AuthenticatedClient | Client,
) -> Any | Error | None:
    """Revoke an API key

    Args:
        api_key_id (UUID):

    Raises:
        grepvine.APIError: The service answered with an error.
        grepvine.TransportError: The request could not be delivered.

    Returns:
        Any | Error
    """

    return sync_detailed(
        api_key_id=api_key_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    api_key_id: UUID,
    *,
    client: AuthenticatedClient | Client,
) -> Response[Any | Error]:
    """Revoke an API key

    Args:
        api_key_id (UUID):

    Raises:
        grepvine.APIError: The service answered with an error.
        grepvine.TransportError: The request could not be delivered.

    Returns:
        Response[Any | Error]
    """

    kwargs = _get_kwargs(
        api_key_id=api_key_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    api_key_id: UUID,
    *,
    client: AuthenticatedClient | Client,
) -> Any | Error | None:
    """Revoke an API key

    Args:
        api_key_id (UUID):

    Raises:
        grepvine.APIError: The service answered with an error.
        grepvine.TransportError: The request could not be delivered.

    Returns:
        Any | Error
    """

    return (
        await asyncio_detailed(
            api_key_id=api_key_id,
            client=client,
        )
    ).parsed
