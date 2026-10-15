from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET

from ...models.api_key_page import APIKeyPage
from ...models.error import Error
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
        "url": "/api-keys",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> APIKeyPage | Error:
    if response.status_code == 200:
        response_200 = APIKeyPage.from_dict(response.json())

        return response_200

    response_default = Error.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[APIKeyPage | Error]:
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
) -> Response[APIKeyPage | Error]:
    """List API keys

    Args:
        amount (int | Unset):  Default: 50.
        page (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[APIKeyPage | Error]
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
) -> APIKeyPage | Error | None:
    """List API keys

    Args:
        amount (int | Unset):  Default: 50.
        page (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        APIKeyPage | Error
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
) -> Response[APIKeyPage | Error]:
    """List API keys

    Args:
        amount (int | Unset):  Default: 50.
        page (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[APIKeyPage | Error]
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
) -> APIKeyPage | Error | None:
    """List API keys

    Args:
        amount (int | Unset):  Default: 50.
        page (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        APIKeyPage | Error
    """

    return (
        await asyncio_detailed(
            client=client,
            amount=amount,
            page=page,
        )
    ).parsed
