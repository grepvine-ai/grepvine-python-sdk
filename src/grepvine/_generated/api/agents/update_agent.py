from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response

from ...models.agent import Agent
from ...models.error import Error
from ...models.update_agent_request import UpdateAgentRequest


def _get_kwargs(
    organization: str,
    agent: str,
    *,
    body: UpdateAgentRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "patch",
        "url": "/organizations/{organization}/agents/{agent}".format(
            organization=quote(str(organization), safe=""),
            agent=quote(str(agent), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
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
    *,
    client: AuthenticatedClient | Client,
    body: UpdateAgentRequest,
) -> Response[Agent | Error]:
    """Update an agent

     Changes an agent's description or permissions, or disables or enables it. Its managers, owners and
    admins can change it, and only within their own permissions (and the key's, for a key with
    `manage_agents`); any of them can disable it. New permissions must also be allowed by every
    manager's role, or the change is refused with 409. Saving the permissions of an agent with no
    managers makes you one. A disabled agent is refused everywhere within 10 seconds, with every
    credential it has.

    Args:
        organization (str): A name: of an account, an organization or an agent. Accounts and
            organizations share one namespace; an agent's name is unique within its organization. A
            name keeps the case it was created with, and any spelling that differs only in case refers
            to it; nothing else in the same namespace can take such a spelling.
        agent (str): A name: of an account, an organization or an agent. Accounts and
            organizations share one namespace; an agent's name is unique within its organization. A
            name keeps the case it was created with, and any spelling that differs only in case refers
            to it; nothing else in the same namespace can take such a spelling.
        body (UpdateAgentRequest): The changes to make to an agent. A field left out is kept.

    Raises:
        grepvine.APIError: The service answered with an error.
        grepvine.TransportError: The request could not be delivered.

    Returns:
        Response[Agent | Error]
    """

    kwargs = _get_kwargs(
        organization=organization,
        agent=agent,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    organization: str,
    agent: str,
    *,
    client: AuthenticatedClient | Client,
    body: UpdateAgentRequest,
) -> Agent | Error | None:
    """Update an agent

     Changes an agent's description or permissions, or disables or enables it. Its managers, owners and
    admins can change it, and only within their own permissions (and the key's, for a key with
    `manage_agents`); any of them can disable it. New permissions must also be allowed by every
    manager's role, or the change is refused with 409. Saving the permissions of an agent with no
    managers makes you one. A disabled agent is refused everywhere within 10 seconds, with every
    credential it has.

    Args:
        organization (str): A name: of an account, an organization or an agent. Accounts and
            organizations share one namespace; an agent's name is unique within its organization. A
            name keeps the case it was created with, and any spelling that differs only in case refers
            to it; nothing else in the same namespace can take such a spelling.
        agent (str): A name: of an account, an organization or an agent. Accounts and
            organizations share one namespace; an agent's name is unique within its organization. A
            name keeps the case it was created with, and any spelling that differs only in case refers
            to it; nothing else in the same namespace can take such a spelling.
        body (UpdateAgentRequest): The changes to make to an agent. A field left out is kept.

    Raises:
        grepvine.APIError: The service answered with an error.
        grepvine.TransportError: The request could not be delivered.

    Returns:
        Agent | Error
    """

    return sync_detailed(
        organization=organization,
        agent=agent,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    organization: str,
    agent: str,
    *,
    client: AuthenticatedClient | Client,
    body: UpdateAgentRequest,
) -> Response[Agent | Error]:
    """Update an agent

     Changes an agent's description or permissions, or disables or enables it. Its managers, owners and
    admins can change it, and only within their own permissions (and the key's, for a key with
    `manage_agents`); any of them can disable it. New permissions must also be allowed by every
    manager's role, or the change is refused with 409. Saving the permissions of an agent with no
    managers makes you one. A disabled agent is refused everywhere within 10 seconds, with every
    credential it has.

    Args:
        organization (str): A name: of an account, an organization or an agent. Accounts and
            organizations share one namespace; an agent's name is unique within its organization. A
            name keeps the case it was created with, and any spelling that differs only in case refers
            to it; nothing else in the same namespace can take such a spelling.
        agent (str): A name: of an account, an organization or an agent. Accounts and
            organizations share one namespace; an agent's name is unique within its organization. A
            name keeps the case it was created with, and any spelling that differs only in case refers
            to it; nothing else in the same namespace can take such a spelling.
        body (UpdateAgentRequest): The changes to make to an agent. A field left out is kept.

    Raises:
        grepvine.APIError: The service answered with an error.
        grepvine.TransportError: The request could not be delivered.

    Returns:
        Response[Agent | Error]
    """

    kwargs = _get_kwargs(
        organization=organization,
        agent=agent,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    organization: str,
    agent: str,
    *,
    client: AuthenticatedClient | Client,
    body: UpdateAgentRequest,
) -> Agent | Error | None:
    """Update an agent

     Changes an agent's description or permissions, or disables or enables it. Its managers, owners and
    admins can change it, and only within their own permissions (and the key's, for a key with
    `manage_agents`); any of them can disable it. New permissions must also be allowed by every
    manager's role, or the change is refused with 409. Saving the permissions of an agent with no
    managers makes you one. A disabled agent is refused everywhere within 10 seconds, with every
    credential it has.

    Args:
        organization (str): A name: of an account, an organization or an agent. Accounts and
            organizations share one namespace; an agent's name is unique within its organization. A
            name keeps the case it was created with, and any spelling that differs only in case refers
            to it; nothing else in the same namespace can take such a spelling.
        agent (str): A name: of an account, an organization or an agent. Accounts and
            organizations share one namespace; an agent's name is unique within its organization. A
            name keeps the case it was created with, and any spelling that differs only in case refers
            to it; nothing else in the same namespace can take such a spelling.
        body (UpdateAgentRequest): The changes to make to an agent. A field left out is kept.

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
            client=client,
            body=body,
        )
    ).parsed
