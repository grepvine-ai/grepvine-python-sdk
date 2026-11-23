from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET

from ...models.error import Error
from ...models.organization_usage import OrganizationUsage
from ...models.usage_resolution import UsageResolution
from ...types import Unset


def _get_kwargs(
    organization: str,
    *,
    resolution: UsageResolution,
    index: str | Unset = UNSET,
) -> dict[str, Any]:

    params: dict[str, Any] = {}

    json_resolution = resolution.value
    params["resolution"] = json_resolution

    params["index"] = index

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/organizations/{organization}/usage".format(
            organization=quote(str(organization), safe=""),
        ),
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Error | OrganizationUsage:
    if response.status_code == 200:
        response_200 = OrganizationUsage.from_dict(response.json())

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
) -> Response[Error | OrganizationUsage]:
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
    resolution: UsageResolution,
    index: str | Unset = UNSET,
) -> Response[Error | OrganizationUsage]:
    """Get organization usage

     Returns what the organization stores and the requests it makes, for one index or all of them, over a
    window that
    ends now: the last 24 hours by hour, the last 30 days by day, or the last 12 months by month. Times
    are UTC.
    Requires the owner or admin role; a key needs the `read_usage` permission. Usage can trail activity
    by up to an
    hour.

    Args:
        organization (str): A name: of an account, an organization or an agent. Accounts and
            organizations share one namespace; an agent's name is unique within its organization. A
            name keeps the case it was created with, and any spelling that differs only in case refers
            to it; nothing else in the same namespace can take such a spelling.
        resolution (UsageResolution): The length of a usage bucket.
        index (str | Unset): An index name, unique in its organization. A name keeps the case it
            was created with, and any spelling that differs only in case refers to it; no other index
            in the organization can take such a spelling.

    Raises:
        grepvine.APIError: The service answered with an error.
        grepvine.TransportError: The request could not be delivered.

    Returns:
        Response[Error | OrganizationUsage]
    """

    kwargs = _get_kwargs(
        organization=organization,
        resolution=resolution,
        index=index,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    organization: str,
    *,
    client: AuthenticatedClient | Client,
    resolution: UsageResolution,
    index: str | Unset = UNSET,
) -> Error | OrganizationUsage | None:
    """Get organization usage

     Returns what the organization stores and the requests it makes, for one index or all of them, over a
    window that
    ends now: the last 24 hours by hour, the last 30 days by day, or the last 12 months by month. Times
    are UTC.
    Requires the owner or admin role; a key needs the `read_usage` permission. Usage can trail activity
    by up to an
    hour.

    Args:
        organization (str): A name: of an account, an organization or an agent. Accounts and
            organizations share one namespace; an agent's name is unique within its organization. A
            name keeps the case it was created with, and any spelling that differs only in case refers
            to it; nothing else in the same namespace can take such a spelling.
        resolution (UsageResolution): The length of a usage bucket.
        index (str | Unset): An index name, unique in its organization. A name keeps the case it
            was created with, and any spelling that differs only in case refers to it; no other index
            in the organization can take such a spelling.

    Raises:
        grepvine.APIError: The service answered with an error.
        grepvine.TransportError: The request could not be delivered.

    Returns:
        Error | OrganizationUsage
    """

    return sync_detailed(
        organization=organization,
        client=client,
        resolution=resolution,
        index=index,
    ).parsed


async def asyncio_detailed(
    organization: str,
    *,
    client: AuthenticatedClient | Client,
    resolution: UsageResolution,
    index: str | Unset = UNSET,
) -> Response[Error | OrganizationUsage]:
    """Get organization usage

     Returns what the organization stores and the requests it makes, for one index or all of them, over a
    window that
    ends now: the last 24 hours by hour, the last 30 days by day, or the last 12 months by month. Times
    are UTC.
    Requires the owner or admin role; a key needs the `read_usage` permission. Usage can trail activity
    by up to an
    hour.

    Args:
        organization (str): A name: of an account, an organization or an agent. Accounts and
            organizations share one namespace; an agent's name is unique within its organization. A
            name keeps the case it was created with, and any spelling that differs only in case refers
            to it; nothing else in the same namespace can take such a spelling.
        resolution (UsageResolution): The length of a usage bucket.
        index (str | Unset): An index name, unique in its organization. A name keeps the case it
            was created with, and any spelling that differs only in case refers to it; no other index
            in the organization can take such a spelling.

    Raises:
        grepvine.APIError: The service answered with an error.
        grepvine.TransportError: The request could not be delivered.

    Returns:
        Response[Error | OrganizationUsage]
    """

    kwargs = _get_kwargs(
        organization=organization,
        resolution=resolution,
        index=index,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    organization: str,
    *,
    client: AuthenticatedClient | Client,
    resolution: UsageResolution,
    index: str | Unset = UNSET,
) -> Error | OrganizationUsage | None:
    """Get organization usage

     Returns what the organization stores and the requests it makes, for one index or all of them, over a
    window that
    ends now: the last 24 hours by hour, the last 30 days by day, or the last 12 months by month. Times
    are UTC.
    Requires the owner or admin role; a key needs the `read_usage` permission. Usage can trail activity
    by up to an
    hour.

    Args:
        organization (str): A name: of an account, an organization or an agent. Accounts and
            organizations share one namespace; an agent's name is unique within its organization. A
            name keeps the case it was created with, and any spelling that differs only in case refers
            to it; nothing else in the same namespace can take such a spelling.
        resolution (UsageResolution): The length of a usage bucket.
        index (str | Unset): An index name, unique in its organization. A name keeps the case it
            was created with, and any spelling that differs only in case refers to it; no other index
            in the organization can take such a spelling.

    Raises:
        grepvine.APIError: The service answered with an error.
        grepvine.TransportError: The request could not be delivered.

    Returns:
        Error | OrganizationUsage
    """

    return (
        await asyncio_detailed(
            organization=organization,
            client=client,
            resolution=resolution,
            index=index,
        )
    ).parsed
