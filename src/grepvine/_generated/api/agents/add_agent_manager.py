from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response

from ...models.agent import Agent
from ...models.error import Error


def _get_kwargs(
    organization: str,
    agent: str,
    user: str,
) -> dict[str, Any]:

    _kwargs: dict[str, Any] = {
        "method": "put",
        "url": "/organizations/{organization}/agents/{agent}/managers/{user}".format(
            organization=quote(str(organization), safe=""),
            agent=quote(str(agent), safe=""),
            user=quote(str(user), safe=""),
        ),
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Agent | Error:
    if response.status_code == 200:
        response_200 = Agent.from_dict(response.json())

        return response_200

    if response.status_code == 403:
        response_403 = Error.from_dict(response.json())

        return response_403

    if response.status_code == 404:
        response_404 = Error.from_dict(response.json())

        return response_404

    if response.status_code == 409:
        response_409 = Error.from_dict(response.json())

        return response_409

    response_default = Error.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[Agent | Error]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    organization: str,
    agent: str,
    user: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[Agent | Error]:
    """Add an agent manager

     Makes a member of the organization a manager of the agent. Its managers, owners and admins can add
    one. A 404 means the account is not an active member; a 409, that their role does not allow
    everything the agent may do.

    Args:
        organization (str): A name: of an account, an organization or an agent. Accounts and
            organizations share one namespace; an agent's name is unique within its organization. A
            name keeps the case it was created with, and any spelling that differs only in case refers
            to it; nothing else in the same namespace can take such a spelling.
        agent (str): A name: of an account, an organization or an agent. Accounts and
            organizations share one namespace; an agent's name is unique within its organization. A
            name keeps the case it was created with, and any spelling that differs only in case refers
            to it; nothing else in the same namespace can take such a spelling.
        user (str): A name: of an account, an organization or an agent. Accounts and organizations
            share one namespace; an agent's name is unique within its organization. A name keeps the
            case it was created with, and any spelling that differs only in case refers to it; nothing
            else in the same namespace can take such a spelling.

    Raises:
        grepvine.APIError: The service answered with an error.
        grepvine.TransportError: The request could not be delivered.

    Returns:
        Response[Agent | Error]
    """

    kwargs = _get_kwargs(
        organization=organization,
        agent=agent,
        user=user,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    organization: str,
    agent: str,
    user: str,
    *,
    client: AuthenticatedClient | Client,
) -> Agent | Error | None:
    """Add an agent manager

     Makes a member of the organization a manager of the agent. Its managers, owners and admins can add
    one. A 404 means the account is not an active member; a 409, that their role does not allow
    everything the agent may do.

    Args:
        organization (str): A name: of an account, an organization or an agent. Accounts and
            organizations share one namespace; an agent's name is unique within its organization. A
            name keeps the case it was created with, and any spelling that differs only in case refers
            to it; nothing else in the same namespace can take such a spelling.
        agent (str): A name: of an account, an organization or an agent. Accounts and
            organizations share one namespace; an agent's name is unique within its organization. A
            name keeps the case it was created with, and any spelling that differs only in case refers
            to it; nothing else in the same namespace can take such a spelling.
        user (str): A name: of an account, an organization or an agent. Accounts and organizations
            share one namespace; an agent's name is unique within its organization. A name keeps the
            case it was created with, and any spelling that differs only in case refers to it; nothing
            else in the same namespace can take such a spelling.

    Raises:
        grepvine.APIError: The service answered with an error.
        grepvine.TransportError: The request could not be delivered.

    Returns:
        Agent | Error
    """

    return sync_detailed(
        organization=organization,
        agent=agent,
        user=user,
        client=client,
    ).parsed


async def asyncio_detailed(
    organization: str,
    agent: str,
    user: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[Agent | Error]:
    """Add an agent manager

     Makes a member of the organization a manager of the agent. Its managers, owners and admins can add
    one. A 404 means the account is not an active member; a 409, that their role does not allow
    everything the agent may do.

    Args:
        organization (str): A name: of an account, an organization or an agent. Accounts and
            organizations share one namespace; an agent's name is unique within its organization. A
            name keeps the case it was created with, and any spelling that differs only in case refers
            to it; nothing else in the same namespace can take such a spelling.
        agent (str): A name: of an account, an organization or an agent. Accounts and
            organizations share one namespace; an agent's name is unique within its organization. A
            name keeps the case it was created with, and any spelling that differs only in case refers
            to it; nothing else in the same namespace can take such a spelling.
        user (str): A name: of an account, an organization or an agent. Accounts and organizations
            share one namespace; an agent's name is unique within its organization. A name keeps the
            case it was created with, and any spelling that differs only in case refers to it; nothing
            else in the same namespace can take such a spelling.

    Raises:
        grepvine.APIError: The service answered with an error.
        grepvine.TransportError: The request could not be delivered.

    Returns:
        Response[Agent | Error]
    """

    kwargs = _get_kwargs(
        organization=organization,
        agent=agent,
        user=user,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    organization: str,
    agent: str,
    user: str,
    *,
    client: AuthenticatedClient | Client,
) -> Agent | Error | None:
    """Add an agent manager

     Makes a member of the organization a manager of the agent. Its managers, owners and admins can add
    one. A 404 means the account is not an active member; a 409, that their role does not allow
    everything the agent may do.

    Args:
        organization (str): A name: of an account, an organization or an agent. Accounts and
            organizations share one namespace; an agent's name is unique within its organization. A
            name keeps the case it was created with, and any spelling that differs only in case refers
            to it; nothing else in the same namespace can take such a spelling.
        agent (str): A name: of an account, an organization or an agent. Accounts and
            organizations share one namespace; an agent's name is unique within its organization. A
            name keeps the case it was created with, and any spelling that differs only in case refers
            to it; nothing else in the same namespace can take such a spelling.
        user (str): A name: of an account, an organization or an agent. Accounts and organizations
            share one namespace; an agent's name is unique within its organization. A name keeps the
            case it was created with, and any spelling that differs only in case refers to it; nothing
            else in the same namespace can take such a spelling.

    Raises:
        grepvine.APIError: The service answered with an error.
        grepvine.TransportError: The request could not be delivered.

    Returns:
        Agent | Error
    """

    return (
        await asyncio_detailed(
            organization=organization,
            agent=agent,
            user=user,
            client=client,
        )
    ).parsed
