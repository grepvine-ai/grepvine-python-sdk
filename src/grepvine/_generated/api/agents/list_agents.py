from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET

from ...models.agent_page import AgentPage
from ...models.error import Error
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
        "url": "/organizations/{organization}/agents".format(
            organization=quote(str(organization), safe=""),
        ),
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> AgentPage | Error:
    if response.status_code == 200:
        response_200 = AgentPage.from_dict(response.json())

        return response_200

    if response.status_code == 403:
        response_403 = Error.from_dict(response.json())

        return response_403

    if response.status_code == 404:
        response_404 = Error.from_dict(response.json())

        return response_404

    response_default = Error.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[AgentPage | Error]:
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
) -> Response[AgentPage | Error]:
    """List agents

     Lists an organization's agents, ordered by name. Any member can list them; an agent cannot.

    Args:
        organization (str): A name: of an account, an organization or an agent. Accounts and
            organizations share one namespace; an agent's name is unique within its organization. A
            name keeps the case it was created with, and any spelling that differs only in case refers
            to it; nothing else in the same namespace can take such a spelling.
        amount (int | Unset):  Default: 50.
        page (str | Unset):

    Raises:
        grepvine.APIError: The service answered with an error.
        grepvine.TransportError: The request could not be delivered.

    Returns:
        Response[AgentPage | Error]
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
) -> AgentPage | Error | None:
    """List agents

     Lists an organization's agents, ordered by name. Any member can list them; an agent cannot.

    Args:
        organization (str): A name: of an account, an organization or an agent. Accounts and
            organizations share one namespace; an agent's name is unique within its organization. A
            name keeps the case it was created with, and any spelling that differs only in case refers
            to it; nothing else in the same namespace can take such a spelling.
        amount (int | Unset):  Default: 50.
        page (str | Unset):

    Raises:
        grepvine.APIError: The service answered with an error.
        grepvine.TransportError: The request could not be delivered.

    Returns:
        AgentPage | Error
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
) -> Response[AgentPage | Error]:
    """List agents

     Lists an organization's agents, ordered by name. Any member can list them; an agent cannot.

    Args:
        organization (str): A name: of an account, an organization or an agent. Accounts and
            organizations share one namespace; an agent's name is unique within its organization. A
            name keeps the case it was created with, and any spelling that differs only in case refers
            to it; nothing else in the same namespace can take such a spelling.
        amount (int | Unset):  Default: 50.
        page (str | Unset):

    Raises:
        grepvine.APIError: The service answered with an error.
        grepvine.TransportError: The request could not be delivered.

    Returns:
        Response[AgentPage | Error]
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
) -> AgentPage | Error | None:
    """List agents

     Lists an organization's agents, ordered by name. Any member can list them; an agent cannot.

    Args:
        organization (str): A name: of an account, an organization or an agent. Accounts and
            organizations share one namespace; an agent's name is unique within its organization. A
            name keeps the case it was created with, and any spelling that differs only in case refers
            to it; nothing else in the same namespace can take such a spelling.
        amount (int | Unset):  Default: 50.
        page (str | Unset):

    Raises:
        grepvine.APIError: The service answered with an error.
        grepvine.TransportError: The request could not be delivered.

    Returns:
        AgentPage | Error
    """

    return (
        await asyncio_detailed(
            organization=organization,
            client=client,
            amount=amount,
            page=page,
        )
    ).parsed
