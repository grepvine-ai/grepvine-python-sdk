from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response

from ...models.error import Error


def _get_kwargs(
    organization: str,
) -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "delete",
        "url": "/organizations/{organization}".format(
            organization=quote(str(organization), safe=""),
        ),
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Any | Error:
    if response.status_code == 202:
        response_202 = cast(Any, None)
        return response_202

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
    organization: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[Any | Error]:
    """Delete an organization

    Args:
        organization (str): An account or organization name. Accounts and organizations share one
            namespace. A name keeps the case it was created with, and any spelling that differs only
            in case refers to it; no other account or organization can take such a spelling.

    Raises:
        grepvine.APIError: The service answered with an error.
        grepvine.TransportError: The request could not be delivered.

    Returns:
        Response[Any | Error]
    """

    kwargs = _get_kwargs(
        organization=organization,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    organization: str,
    *,
    client: AuthenticatedClient | Client,
) -> Any | Error | None:
    """Delete an organization

    Args:
        organization (str): An account or organization name. Accounts and organizations share one
            namespace. A name keeps the case it was created with, and any spelling that differs only
            in case refers to it; no other account or organization can take such a spelling.

    Raises:
        grepvine.APIError: The service answered with an error.
        grepvine.TransportError: The request could not be delivered.

    Returns:
        Any | Error
    """

    return sync_detailed(
        organization=organization,
        client=client,
    ).parsed


async def asyncio_detailed(
    organization: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[Any | Error]:
    """Delete an organization

    Args:
        organization (str): An account or organization name. Accounts and organizations share one
            namespace. A name keeps the case it was created with, and any spelling that differs only
            in case refers to it; no other account or organization can take such a spelling.

    Raises:
        grepvine.APIError: The service answered with an error.
        grepvine.TransportError: The request could not be delivered.

    Returns:
        Response[Any | Error]
    """

    kwargs = _get_kwargs(
        organization=organization,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    organization: str,
    *,
    client: AuthenticatedClient | Client,
) -> Any | Error | None:
    """Delete an organization

    Args:
        organization (str): An account or organization name. Accounts and organizations share one
            namespace. A name keeps the case it was created with, and any spelling that differs only
            in case refers to it; no other account or organization can take such a spelling.

    Raises:
        grepvine.APIError: The service answered with an error.
        grepvine.TransportError: The request could not be delivered.

    Returns:
        Any | Error
    """

    return (
        await asyncio_detailed(
            organization=organization,
            client=client,
        )
    ).parsed
