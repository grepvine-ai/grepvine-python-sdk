from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET

from ...models.error import Error
from ...models.query_page import QueryPage
from ...models.query_request import QueryRequest
from ...types import Unset


def _get_kwargs(
    organization: str,
    index: str,
    *,
    body: QueryRequest,
    amount: int | Unset = 50,
    page: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    params: dict[str, Any] = {}

    params["amount"] = amount

    params["page"] = page

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/organizations/{organization}/indexes/{index}/query".format(
            organization=quote(str(organization), safe=""),
            index=quote(str(index), safe=""),
        ),
        "params": params,
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Error | QueryPage:
    if response.status_code == 200:
        response_200 = QueryPage.from_dict(response.json())

        return response_200

    response_default = Error.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[Error | QueryPage]:
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
    body: QueryRequest,
    amount: int | Unset = 50,
    page: str | Unset = UNSET,
) -> Response[Error | QueryPage]:
    """Search an index

    Args:
        organization (str): An account or organization name. Accounts and organizations share one
            namespace. A name keeps the case it was created with, and any spelling that differs only
            in case refers to it; no other account or organization can take such a spelling.
        index (str): An index name, unique in its organization. A name keeps the case it was
            created with, and any spelling that differs only in case refers to it; no other index in
            the organization can take such a spelling.
        amount (int | Unset):  Default: 50.
        page (str | Unset):
        body (QueryRequest):

    Raises:
        grepvine.APIError: The service answered with an error.
        grepvine.TransportError: The request could not be delivered.

    Returns:
        Response[Error | QueryPage]
    """

    kwargs = _get_kwargs(
        organization=organization,
        index=index,
        body=body,
        amount=amount,
        page=page,
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
    body: QueryRequest,
    amount: int | Unset = 50,
    page: str | Unset = UNSET,
) -> Error | QueryPage | None:
    """Search an index

    Args:
        organization (str): An account or organization name. Accounts and organizations share one
            namespace. A name keeps the case it was created with, and any spelling that differs only
            in case refers to it; no other account or organization can take such a spelling.
        index (str): An index name, unique in its organization. A name keeps the case it was
            created with, and any spelling that differs only in case refers to it; no other index in
            the organization can take such a spelling.
        amount (int | Unset):  Default: 50.
        page (str | Unset):
        body (QueryRequest):

    Raises:
        grepvine.APIError: The service answered with an error.
        grepvine.TransportError: The request could not be delivered.

    Returns:
        Error | QueryPage
    """

    return sync_detailed(
        organization=organization,
        index=index,
        client=client,
        body=body,
        amount=amount,
        page=page,
    ).parsed


async def asyncio_detailed(
    organization: str,
    index: str,
    *,
    client: AuthenticatedClient | Client,
    body: QueryRequest,
    amount: int | Unset = 50,
    page: str | Unset = UNSET,
) -> Response[Error | QueryPage]:
    """Search an index

    Args:
        organization (str): An account or organization name. Accounts and organizations share one
            namespace. A name keeps the case it was created with, and any spelling that differs only
            in case refers to it; no other account or organization can take such a spelling.
        index (str): An index name, unique in its organization. A name keeps the case it was
            created with, and any spelling that differs only in case refers to it; no other index in
            the organization can take such a spelling.
        amount (int | Unset):  Default: 50.
        page (str | Unset):
        body (QueryRequest):

    Raises:
        grepvine.APIError: The service answered with an error.
        grepvine.TransportError: The request could not be delivered.

    Returns:
        Response[Error | QueryPage]
    """

    kwargs = _get_kwargs(
        organization=organization,
        index=index,
        body=body,
        amount=amount,
        page=page,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    organization: str,
    index: str,
    *,
    client: AuthenticatedClient | Client,
    body: QueryRequest,
    amount: int | Unset = 50,
    page: str | Unset = UNSET,
) -> Error | QueryPage | None:
    """Search an index

    Args:
        organization (str): An account or organization name. Accounts and organizations share one
            namespace. A name keeps the case it was created with, and any spelling that differs only
            in case refers to it; no other account or organization can take such a spelling.
        index (str): An index name, unique in its organization. A name keeps the case it was
            created with, and any spelling that differs only in case refers to it; no other index in
            the organization can take such a spelling.
        amount (int | Unset):  Default: 50.
        page (str | Unset):
        body (QueryRequest):

    Raises:
        grepvine.APIError: The service answered with an error.
        grepvine.TransportError: The request could not be delivered.

    Returns:
        Error | QueryPage
    """

    return (
        await asyncio_detailed(
            organization=organization,
            index=index,
            client=client,
            body=body,
            amount=amount,
            page=page,
        )
    ).parsed
