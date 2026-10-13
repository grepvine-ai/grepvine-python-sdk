from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET

from ...models.error import Error
from ...models.index import Index
from ...models.update_index_request import UpdateIndexRequest
from ...types import Unset


def _get_kwargs(
    organization: str,
    index: str,
    *,
    body: UpdateIndexRequest,
    x_csrf_token: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    if not isinstance(x_csrf_token, Unset):
        headers["X-Csrf-Token"] = x_csrf_token

    _kwargs: dict[str, Any] = {
        "method": "patch",
        "url": "/organizations/{organization}/indexes/{index}".format(
            organization=quote(str(organization), safe=""),
            index=quote(str(index), safe=""),
        ),
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Error | Index:
    if response.status_code == 200:
        response_200 = Index.from_dict(response.json())

        return response_200

    if response.status_code == 404:
        response_404 = Error.from_dict(response.json())

        return response_404

    response_default = Error.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[Error | Index]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    organization: str,
    index: str,
    *,
    client: AuthenticatedClient | Client,
    body: UpdateIndexRequest,
    x_csrf_token: str | Unset = UNSET,
) -> Response[Error | Index]:
    """Update an index

     Changes the index's description or tags. A field absent from the request is left as it is. The name
    is immutable.

    Args:
        organization (str): An account or organization name. Accounts and organizations share one
            namespace. A name keeps the case it was created with, and any spelling that differs only
            in case refers to it; no other account or organization can take such a spelling.
        index (str): An index name, unique in its organization. A name keeps the case it was
            created with, and any spelling that differs only in case refers to it; no other index in
            the organization can take such a spelling.
        x_csrf_token (str | Unset):
        body (UpdateIndexRequest): The fields to change. A field that is absent is left as it is;
            at least one must be present.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Error | Index]
    """

    kwargs = _get_kwargs(
        organization=organization,
        index=index,
        body=body,
        x_csrf_token=x_csrf_token,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    organization: str,
    index: str,
    *,
    client: AuthenticatedClient | Client,
    body: UpdateIndexRequest,
    x_csrf_token: str | Unset = UNSET,
) -> Error | Index | None:
    """Update an index

     Changes the index's description or tags. A field absent from the request is left as it is. The name
    is immutable.

    Args:
        organization (str): An account or organization name. Accounts and organizations share one
            namespace. A name keeps the case it was created with, and any spelling that differs only
            in case refers to it; no other account or organization can take such a spelling.
        index (str): An index name, unique in its organization. A name keeps the case it was
            created with, and any spelling that differs only in case refers to it; no other index in
            the organization can take such a spelling.
        x_csrf_token (str | Unset):
        body (UpdateIndexRequest): The fields to change. A field that is absent is left as it is;
            at least one must be present.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Error | Index
    """

    return sync_detailed(
        organization=organization,
        index=index,
        client=client,
        body=body,
        x_csrf_token=x_csrf_token,
    ).parsed


async def asyncio_detailed(
    organization: str,
    index: str,
    *,
    client: AuthenticatedClient | Client,
    body: UpdateIndexRequest,
    x_csrf_token: str | Unset = UNSET,
) -> Response[Error | Index]:
    """Update an index

     Changes the index's description or tags. A field absent from the request is left as it is. The name
    is immutable.

    Args:
        organization (str): An account or organization name. Accounts and organizations share one
            namespace. A name keeps the case it was created with, and any spelling that differs only
            in case refers to it; no other account or organization can take such a spelling.
        index (str): An index name, unique in its organization. A name keeps the case it was
            created with, and any spelling that differs only in case refers to it; no other index in
            the organization can take such a spelling.
        x_csrf_token (str | Unset):
        body (UpdateIndexRequest): The fields to change. A field that is absent is left as it is;
            at least one must be present.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Error | Index]
    """

    kwargs = _get_kwargs(
        organization=organization,
        index=index,
        body=body,
        x_csrf_token=x_csrf_token,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    organization: str,
    index: str,
    *,
    client: AuthenticatedClient | Client,
    body: UpdateIndexRequest,
    x_csrf_token: str | Unset = UNSET,
) -> Error | Index | None:
    """Update an index

     Changes the index's description or tags. A field absent from the request is left as it is. The name
    is immutable.

    Args:
        organization (str): An account or organization name. Accounts and organizations share one
            namespace. A name keeps the case it was created with, and any spelling that differs only
            in case refers to it; no other account or organization can take such a spelling.
        index (str): An index name, unique in its organization. A name keeps the case it was
            created with, and any spelling that differs only in case refers to it; no other index in
            the organization can take such a spelling.
        x_csrf_token (str | Unset):
        body (UpdateIndexRequest): The fields to change. A field that is absent is left as it is;
            at least one must be present.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Error | Index
    """

    return (
        await asyncio_detailed(
            organization=organization,
            index=index,
            client=client,
            body=body,
            x_csrf_token=x_csrf_token,
        )
    ).parsed
