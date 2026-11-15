from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response

from ...models.agent_secret_created import AgentSecretCreated
from ...models.create_agent_secret_request import CreateAgentSecretRequest
from ...models.error import Error


def _get_kwargs(
    organization: str,
    agent: str,
    *,
    body: CreateAgentSecretRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/organizations/{organization}/agents/{agent}/secrets".format(
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
) -> AgentSecretCreated | Error:
    if response.status_code == 201:
        response_201 = AgentSecretCreated.from_dict(response.json())

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
) -> Response[AgentSecretCreated | Error]:
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
    body: CreateAgentSecretRequest,
) -> Response[AgentSecretCreated | Error]:
    """Create an agent secret

     Creates a secret the agent signs in with. An agent has at most two, so one can replace the other; a
    409 asks you to remove one first. Its managers, owners and admins can create one, and only from a
    signed-in session. The response is the only time the secret is shown, so store it securely.

    Args:
        organization (str): A name: of an account, an organization or an agent. Accounts and
            organizations share one namespace; an agent's name is unique within its organization. A
            name keeps the case it was created with, and any spelling that differs only in case refers
            to it; nothing else in the same namespace can take such a spelling.
        agent (str): A name: of an account, an organization or an agent. Accounts and
            organizations share one namespace; an agent's name is unique within its organization. A
            name keeps the case it was created with, and any spelling that differs only in case refers
            to it; nothing else in the same namespace can take such a spelling.
        body (CreateAgentSecretRequest): A new agent secret.

    Raises:
        grepvine.APIError: The service answered with an error.
        grepvine.TransportError: The request could not be delivered.

    Returns:
        Response[AgentSecretCreated | Error]
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
    body: CreateAgentSecretRequest,
) -> AgentSecretCreated | Error | None:
    """Create an agent secret

     Creates a secret the agent signs in with. An agent has at most two, so one can replace the other; a
    409 asks you to remove one first. Its managers, owners and admins can create one, and only from a
    signed-in session. The response is the only time the secret is shown, so store it securely.

    Args:
        organization (str): A name: of an account, an organization or an agent. Accounts and
            organizations share one namespace; an agent's name is unique within its organization. A
            name keeps the case it was created with, and any spelling that differs only in case refers
            to it; nothing else in the same namespace can take such a spelling.
        agent (str): A name: of an account, an organization or an agent. Accounts and
            organizations share one namespace; an agent's name is unique within its organization. A
            name keeps the case it was created with, and any spelling that differs only in case refers
            to it; nothing else in the same namespace can take such a spelling.
        body (CreateAgentSecretRequest): A new agent secret.

    Raises:
        grepvine.APIError: The service answered with an error.
        grepvine.TransportError: The request could not be delivered.

    Returns:
        AgentSecretCreated | Error
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
    body: CreateAgentSecretRequest,
) -> Response[AgentSecretCreated | Error]:
    """Create an agent secret

     Creates a secret the agent signs in with. An agent has at most two, so one can replace the other; a
    409 asks you to remove one first. Its managers, owners and admins can create one, and only from a
    signed-in session. The response is the only time the secret is shown, so store it securely.

    Args:
        organization (str): A name: of an account, an organization or an agent. Accounts and
            organizations share one namespace; an agent's name is unique within its organization. A
            name keeps the case it was created with, and any spelling that differs only in case refers
            to it; nothing else in the same namespace can take such a spelling.
        agent (str): A name: of an account, an organization or an agent. Accounts and
            organizations share one namespace; an agent's name is unique within its organization. A
            name keeps the case it was created with, and any spelling that differs only in case refers
            to it; nothing else in the same namespace can take such a spelling.
        body (CreateAgentSecretRequest): A new agent secret.

    Raises:
        grepvine.APIError: The service answered with an error.
        grepvine.TransportError: The request could not be delivered.

    Returns:
        Response[AgentSecretCreated | Error]
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
    body: CreateAgentSecretRequest,
) -> AgentSecretCreated | Error | None:
    """Create an agent secret

     Creates a secret the agent signs in with. An agent has at most two, so one can replace the other; a
    409 asks you to remove one first. Its managers, owners and admins can create one, and only from a
    signed-in session. The response is the only time the secret is shown, so store it securely.

    Args:
        organization (str): A name: of an account, an organization or an agent. Accounts and
            organizations share one namespace; an agent's name is unique within its organization. A
            name keeps the case it was created with, and any spelling that differs only in case refers
            to it; nothing else in the same namespace can take such a spelling.
        agent (str): A name: of an account, an organization or an agent. Accounts and
            organizations share one namespace; an agent's name is unique within its organization. A
            name keeps the case it was created with, and any spelling that differs only in case refers
            to it; nothing else in the same namespace can take such a spelling.
        body (CreateAgentSecretRequest): A new agent secret.

    Raises:
        grepvine.APIError: The service answered with an error.
        grepvine.TransportError: The request could not be delivered.

    Returns:
        AgentSecretCreated | Error
    """

    return (
        await asyncio_detailed(
            organization=organization,
            agent=agent,
            client=client,
            body=body,
        )
    ).parsed
