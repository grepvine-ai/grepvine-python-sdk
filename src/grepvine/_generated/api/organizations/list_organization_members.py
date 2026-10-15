from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET

from ...models.error import Error
from ...models.member_page import MemberPage
from ...types import Unset


def _get_kwargs(
    organization: str,
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
        "url": "/organizations/{organization}/members".format(
            organization=quote(str(organization), safe=""),
        ),
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Error | MemberPage:
    if response.status_code == 200:
        response_200 = MemberPage.from_dict(response.json())

        return response_200

    response_default = Error.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[Error | MemberPage]:
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
    amount: int | Unset = 50,
    page: str | Unset = UNSET,
) -> Response[Error | MemberPage]:
    """List organization members

    Args:
        organization (str): An account or organization name. Accounts and organizations share one
            namespace. A name keeps the case it was created with, and any spelling that differs only
            in case refers to it; no other account or organization can take such a spelling.
        amount (int | Unset):  Default: 50.
        page (str | Unset):

    Raises:
        grepvine.APIError: The service answered with an error.
        grepvine.TransportError: The request could not be delivered.

    Returns:
        Response[Error | MemberPage]
    """

    kwargs = _get_kwargs(
        organization=organization,
        amount=amount,
        page=page,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    organization: str,
    *,
    client: AuthenticatedClient | Client,
    amount: int | Unset = 50,
    page: str | Unset = UNSET,
) -> Error | MemberPage | None:
    """List organization members

    Args:
        organization (str): An account or organization name. Accounts and organizations share one
            namespace. A name keeps the case it was created with, and any spelling that differs only
            in case refers to it; no other account or organization can take such a spelling.
        amount (int | Unset):  Default: 50.
        page (str | Unset):

    Raises:
        grepvine.APIError: The service answered with an error.
        grepvine.TransportError: The request could not be delivered.

    Returns:
        Error | MemberPage
    """

    return sync_detailed(
        organization=organization,
        client=client,
        amount=amount,
        page=page,
    ).parsed


async def asyncio_detailed(
    organization: str,
    *,
    client: AuthenticatedClient | Client,
    amount: int | Unset = 50,
    page: str | Unset = UNSET,
) -> Response[Error | MemberPage]:
    """List organization members

    Args:
        organization (str): An account or organization name. Accounts and organizations share one
            namespace. A name keeps the case it was created with, and any spelling that differs only
            in case refers to it; no other account or organization can take such a spelling.
        amount (int | Unset):  Default: 50.
        page (str | Unset):

    Raises:
        grepvine.APIError: The service answered with an error.
        grepvine.TransportError: The request could not be delivered.

    Returns:
        Response[Error | MemberPage]
    """

    kwargs = _get_kwargs(
        organization=organization,
        amount=amount,
        page=page,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    organization: str,
    *,
    client: AuthenticatedClient | Client,
    amount: int | Unset = 50,
    page: str | Unset = UNSET,
) -> Error | MemberPage | None:
    """List organization members

    Args:
        organization (str): An account or organization name. Accounts and organizations share one
            namespace. A name keeps the case it was created with, and any spelling that differs only
            in case refers to it; no other account or organization can take such a spelling.
        amount (int | Unset):  Default: 50.
        page (str | Unset):

    Raises:
        grepvine.APIError: The service answered with an error.
        grepvine.TransportError: The request could not be delivered.

    Returns:
        Error | MemberPage
    """

    return (
        await asyncio_detailed(
            organization=organization,
            client=client,
            amount=amount,
            page=page,
        )
    ).parsed
