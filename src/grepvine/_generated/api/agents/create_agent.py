from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response

from ...models.agent import Agent
from ...models.create_agent_request import CreateAgentRequest
from ...models.error import Error


def _get_kwargs(
    organization: str,
    *,
    body: CreateAgentRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/organizations/{organization}/agents".format(
            organization=quote(str(organization), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Agent | Error:
    if response.status_code == 201:
        response_201 = Agent.from_dict(response.json())

        return response_201

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
    *,
    client: AuthenticatedClient | Client,
    body: CreateAgentRequest,
) -> Response[Agent | Error]:
    """Create an agent

     Creates an agent, with the creator as its first manager. Owners and admins can create agents, and
    developers too when the organization allows it. The agent's permissions must be within your own, and
    within the key's when a key creates it; a key needs `manage_agents`. A 409 means the organization
    already has an agent of that name, in any case.

    Args:
        organization (str): A name: of an account, an organization or an agent. Accounts and
            organizations share one namespace; an agent's name is unique within its organization. A
            name keeps the case it was created with, and any spelling that differs only in case refers
            to it; nothing else in the same namespace can take such a spelling.
        body (CreateAgentRequest): A new agent. Leave indexes out for every index of the
            organization, including indexes created later.

    Raises:
        grepvine.APIError: The service answered with an error.
        grepvine.TransportError: The request could not be delivered.

    Returns:
        Response[Agent | Error]
    """

    kwargs = _get_kwargs(
        organization=organization,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    organization: str,
    *,
    client: AuthenticatedClient | Client,
    body: CreateAgentRequest,
) -> Agent | Error | None:
    """Create an agent

     Creates an agent, with the creator as its first manager. Owners and admins can create agents, and
    developers too when the organization allows it. The agent's permissions must be within your own, and
    within the key's when a key creates it; a key needs `manage_agents`. A 409 means the organization
    already has an agent of that name, in any case.

    Args:
        organization (str): A name: of an account, an organization or an agent. Accounts and
            organizations share one namespace; an agent's name is unique within its organization. A
            name keeps the case it was created with, and any spelling that differs only in case refers
            to it; nothing else in the same namespace can take such a spelling.
        body (CreateAgentRequest): A new agent. Leave indexes out for every index of the
            organization, including indexes created later.

    Raises:
        grepvine.APIError: The service answered with an error.
        grepvine.TransportError: The request could not be delivered.

    Returns:
        Agent | Error
    """

    return sync_detailed(
        organization=organization,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    organization: str,
    *,
    client: AuthenticatedClient | Client,
    body: CreateAgentRequest,
) -> Response[Agent | Error]:
    """Create an agent

     Creates an agent, with the creator as its first manager. Owners and admins can create agents, and
    developers too when the organization allows it. The agent's permissions must be within your own, and
    within the key's when a key creates it; a key needs `manage_agents`. A 409 means the organization
    already has an agent of that name, in any case.

    Args:
        organization (str): A name: of an account, an organization or an agent. Accounts and
            organizations share one namespace; an agent's name is unique within its organization. A
            name keeps the case it was created with, and any spelling that differs only in case refers
            to it; nothing else in the same namespace can take such a spelling.
        body (CreateAgentRequest): A new agent. Leave indexes out for every index of the
            organization, including indexes created later.

    Raises:
        grepvine.APIError: The service answered with an error.
        grepvine.TransportError: The request could not be delivered.

    Returns:
        Response[Agent | Error]
    """

    kwargs = _get_kwargs(
        organization=organization,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    organization: str,
    *,
    client: AuthenticatedClient | Client,
    body: CreateAgentRequest,
) -> Agent | Error | None:
    """Create an agent

     Creates an agent, with the creator as its first manager. Owners and admins can create agents, and
    developers too when the organization allows it. The agent's permissions must be within your own, and
    within the key's when a key creates it; a key needs `manage_agents`. A 409 means the organization
    already has an agent of that name, in any case.

    Args:
        organization (str): A name: of an account, an organization or an agent. Accounts and
            organizations share one namespace; an agent's name is unique within its organization. A
            name keeps the case it was created with, and any spelling that differs only in case refers
            to it; nothing else in the same namespace can take such a spelling.
        body (CreateAgentRequest): A new agent. Leave indexes out for every index of the
            organization, including indexes created later.

    Raises:
        grepvine.APIError: The service answered with an error.
        grepvine.TransportError: The request could not be delivered.

    Returns:
        Agent | Error
    """

    return (
        await asyncio_detailed(
            organization=organization,
            client=client,
            body=body,
        )
    ).parsed
