from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response

from ...models.error import Error
from ...models.organization import Organization
from ...models.update_organization_request import UpdateOrganizationRequest


def _get_kwargs(
    organization: str,
    *,
    body: UpdateOrganizationRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "patch",
        "url": "/organizations/{organization}".format(
            organization=quote(str(organization), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Error | Organization:
    if response.status_code == 200:
        response_200 = Organization.from_dict(response.json())

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
) -> Response[Error | Organization]:
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
    body: UpdateOrganizationRequest,
) -> Response[Error | Organization]:
    """Update an organization

     Changes an organization's settings. Requires the owner or admin role, and only a signed-in session
    can change them.

    Args:
        organization (str): A name: of an account, an organization or an agent. Accounts and
            organizations share one namespace; an agent's name is unique within its organization. A
            name keeps the case it was created with, and any spelling that differs only in case refers
            to it; nothing else in the same namespace can take such a spelling.
        body (UpdateOrganizationRequest): The settings to change. A field left out is kept.

    Raises:
        grepvine.APIError: The service answered with an error.
        grepvine.TransportError: The request could not be delivered.

    Returns:
        Response[Error | Organization]
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
    body: UpdateOrganizationRequest,
) -> Error | Organization | None:
    """Update an organization

     Changes an organization's settings. Requires the owner or admin role, and only a signed-in session
    can change them.

    Args:
        organization (str): A name: of an account, an organization or an agent. Accounts and
            organizations share one namespace; an agent's name is unique within its organization. A
            name keeps the case it was created with, and any spelling that differs only in case refers
            to it; nothing else in the same namespace can take such a spelling.
        body (UpdateOrganizationRequest): The settings to change. A field left out is kept.

    Raises:
        grepvine.APIError: The service answered with an error.
        grepvine.TransportError: The request could not be delivered.

    Returns:
        Error | Organization
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
    body: UpdateOrganizationRequest,
) -> Response[Error | Organization]:
    """Update an organization

     Changes an organization's settings. Requires the owner or admin role, and only a signed-in session
    can change them.

    Args:
        organization (str): A name: of an account, an organization or an agent. Accounts and
            organizations share one namespace; an agent's name is unique within its organization. A
            name keeps the case it was created with, and any spelling that differs only in case refers
            to it; nothing else in the same namespace can take such a spelling.
        body (UpdateOrganizationRequest): The settings to change. A field left out is kept.

    Raises:
        grepvine.APIError: The service answered with an error.
        grepvine.TransportError: The request could not be delivered.

    Returns:
        Response[Error | Organization]
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
    body: UpdateOrganizationRequest,
) -> Error | Organization | None:
    """Update an organization

     Changes an organization's settings. Requires the owner or admin role, and only a signed-in session
    can change them.

    Args:
        organization (str): A name: of an account, an organization or an agent. Accounts and
            organizations share one namespace; an agent's name is unique within its organization. A
            name keeps the case it was created with, and any spelling that differs only in case refers
            to it; nothing else in the same namespace can take such a spelling.
        body (UpdateOrganizationRequest): The settings to change. A field left out is kept.

    Raises:
        grepvine.APIError: The service answered with an error.
        grepvine.TransportError: The request could not be delivered.

    Returns:
        Error | Organization
    """

    return (
        await asyncio_detailed(
            organization=organization,
            client=client,
            body=body,
        )
    ).parsed
