from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET

from ...models.error import Error
from ...models.organization_page import OrganizationPage
from ...types import Unset


def _get_kwargs(
    *,
    amount: int | Unset = 50,
    page: str | Unset = UNSET,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    params["amount"] = amount

    params["page"] = page

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/organizations",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Error | OrganizationPage:
    if response.status_code == 200:
        response_200 = OrganizationPage.from_dict(response.json())

        return response_200

    response_default = Error.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[Error | OrganizationPage]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    amount: int | Unset = 50,
    page: str | Unset = UNSET,
) -> Response[Error | OrganizationPage]:
    """List organizations

    Args:
        amount (int | Unset):  Default: 50.
        page (str | Unset):

    Raises:
        grepvine.APIError: The service answered with an error.
        grepvine.TransportError: The request could not be delivered.

    Returns:
        Response[Error | OrganizationPage]
    """

    kwargs = _get_kwargs(
        amount=amount,
        page=page,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    amount: int | Unset = 50,
    page: str | Unset = UNSET,
) -> Error | OrganizationPage | None:
    """List organizations

    Args:
        amount (int | Unset):  Default: 50.
        page (str | Unset):

    Raises:
        grepvine.APIError: The service answered with an error.
        grepvine.TransportError: The request could not be delivered.

    Returns:
        Error | OrganizationPage
    """

    return sync_detailed(
        client=client,
        amount=amount,
        page=page,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    amount: int | Unset = 50,
    page: str | Unset = UNSET,
) -> Response[Error | OrganizationPage]:
    """List organizations

    Args:
        amount (int | Unset):  Default: 50.
        page (str | Unset):

    Raises:
        grepvine.APIError: The service answered with an error.
        grepvine.TransportError: The request could not be delivered.

    Returns:
        Response[Error | OrganizationPage]
    """

    kwargs = _get_kwargs(
        amount=amount,
        page=page,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    amount: int | Unset = 50,
    page: str | Unset = UNSET,
) -> Error | OrganizationPage | None:
    """List organizations

    Args:
        amount (int | Unset):  Default: 50.
        page (str | Unset):

    Raises:
        grepvine.APIError: The service answered with an error.
        grepvine.TransportError: The request could not be delivered.

    Returns:
        Error | OrganizationPage
    """

    return (
        await asyncio_detailed(
            client=client,
            amount=amount,
            page=page,
        )
    ).parsed
