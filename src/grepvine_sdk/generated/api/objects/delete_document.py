from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET

from ...models.error import Error
from ...models.mutation_result import MutationResult
from ...types import Unset


def _get_kwargs(
    organization: str,
    index: str,
    key: str,
    *,
    idempotency_key: str,
    if_match: str | Unset = UNSET,
    x_csrf_token: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["Idempotency-Key"] = idempotency_key

    if not isinstance(if_match, Unset):
        headers["If-Match"] = if_match

    if not isinstance(x_csrf_token, Unset):
        headers["X-Csrf-Token"] = x_csrf_token

    _kwargs: dict[str, Any] = {
        "method": "delete",
        "url": "/organizations/{organization}/indexes/{index}/objects/{key}".format(
            organization=quote(str(organization), safe=""),
            index=quote(str(index), safe=""),
            key=quote(str(key), safe=""),
        ),
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Error | MutationResult:
    if response.status_code == 200:
        response_200 = MutationResult.from_dict(response.json())

        return response_200

    if response.status_code == 404:
        response_404 = Error.from_dict(response.json())

        return response_404

    if response.status_code == 412:
        response_412 = Error.from_dict(response.json())

        return response_412

    response_default = Error.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[Error | MutationResult]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    organization: str,
    index: str,
    key: str,
    *,
    client: AuthenticatedClient | Client,
    idempotency_key: str,
    if_match: str | Unset = UNSET,
    x_csrf_token: str | Unset = UNSET,
) -> Response[Error | MutationResult]:
    """Delete one document

    Args:
        organization (str): An account or organization name. Accounts and organizations share one
            namespace. A name keeps the case it was created with, and any spelling that differs only
            in case refers to it; no other account or organization can take such a spelling.
        index (str): An index name, unique in its organization. A name keeps the case it was
            created with, and any spelling that differs only in case refers to it; no other index in
            the organization can take such a spelling.
        key (str):
        idempotency_key (str):
        if_match (str | Unset):
        x_csrf_token (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Error | MutationResult]
    """

    kwargs = _get_kwargs(
        organization=organization,
        index=index,
        key=key,
        idempotency_key=idempotency_key,
        if_match=if_match,
        x_csrf_token=x_csrf_token,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    organization: str,
    index: str,
    key: str,
    *,
    client: AuthenticatedClient | Client,
    idempotency_key: str,
    if_match: str | Unset = UNSET,
    x_csrf_token: str | Unset = UNSET,
) -> Error | MutationResult | None:
    """Delete one document

    Args:
        organization (str): An account or organization name. Accounts and organizations share one
            namespace. A name keeps the case it was created with, and any spelling that differs only
            in case refers to it; no other account or organization can take such a spelling.
        index (str): An index name, unique in its organization. A name keeps the case it was
            created with, and any spelling that differs only in case refers to it; no other index in
            the organization can take such a spelling.
        key (str):
        idempotency_key (str):
        if_match (str | Unset):
        x_csrf_token (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Error | MutationResult
    """

    return sync_detailed(
        organization=organization,
        index=index,
        key=key,
        client=client,
        idempotency_key=idempotency_key,
        if_match=if_match,
        x_csrf_token=x_csrf_token,
    ).parsed


async def asyncio_detailed(
    organization: str,
    index: str,
    key: str,
    *,
    client: AuthenticatedClient | Client,
    idempotency_key: str,
    if_match: str | Unset = UNSET,
    x_csrf_token: str | Unset = UNSET,
) -> Response[Error | MutationResult]:
    """Delete one document

    Args:
        organization (str): An account or organization name. Accounts and organizations share one
            namespace. A name keeps the case it was created with, and any spelling that differs only
            in case refers to it; no other account or organization can take such a spelling.
        index (str): An index name, unique in its organization. A name keeps the case it was
            created with, and any spelling that differs only in case refers to it; no other index in
            the organization can take such a spelling.
        key (str):
        idempotency_key (str):
        if_match (str | Unset):
        x_csrf_token (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Error | MutationResult]
    """

    kwargs = _get_kwargs(
        organization=organization,
        index=index,
        key=key,
        idempotency_key=idempotency_key,
        if_match=if_match,
        x_csrf_token=x_csrf_token,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    organization: str,
    index: str,
    key: str,
    *,
    client: AuthenticatedClient | Client,
    idempotency_key: str,
    if_match: str | Unset = UNSET,
    x_csrf_token: str | Unset = UNSET,
) -> Error | MutationResult | None:
    """Delete one document

    Args:
        organization (str): An account or organization name. Accounts and organizations share one
            namespace. A name keeps the case it was created with, and any spelling that differs only
            in case refers to it; no other account or organization can take such a spelling.
        index (str): An index name, unique in its organization. A name keeps the case it was
            created with, and any spelling that differs only in case refers to it; no other index in
            the organization can take such a spelling.
        key (str):
        idempotency_key (str):
        if_match (str | Unset):
        x_csrf_token (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Error | MutationResult
    """

    return (
        await asyncio_detailed(
            organization=organization,
            index=index,
            key=key,
            client=client,
            idempotency_key=idempotency_key,
            if_match=if_match,
            x_csrf_token=x_csrf_token,
        )
    ).parsed
