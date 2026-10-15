from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET

from ...models.error import Error
from ...models.mutation_result import MutationResult
from ...models.put_document_form import PutDocumentForm
from ...models.put_document_if_none_match import PutDocumentIfNoneMatch
from ...types import Unset


def _get_kwargs(
    organization: str,
    index: str,
    *,
    body: PutDocumentForm,
    idempotency_key: str,
    if_match: str | Unset = UNSET,
    if_none_match: PutDocumentIfNoneMatch | Unset = UNSET,
    x_csrf_token: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["Idempotency-Key"] = idempotency_key

    if not isinstance(if_match, Unset):
        headers["If-Match"] = if_match

    if not isinstance(if_none_match, Unset):
        headers["If-None-Match"] = str(if_none_match)

    if not isinstance(x_csrf_token, Unset):
        headers["X-Csrf-Token"] = x_csrf_token

    _kwargs: dict[str, Any] = {
        "method": "put",
        "url": "/organizations/{organization}/indexes/{index}/objects".format(
            organization=quote(str(organization), safe=""),
            index=quote(str(index), safe=""),
        ),
    }

    _kwargs["files"] = body.to_multipart()

    headers["Content-Type"] = "multipart/form-data; boundary=+++"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Error | MutationResult:
    if response.status_code == 200:
        response_200 = MutationResult.from_dict(response.json())

        return response_200

    if response.status_code == 409:
        response_409 = Error.from_dict(response.json())

        return response_409

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
    *,
    client: AuthenticatedClient | Client,
    body: PutDocumentForm,
    idempotency_key: str,
    if_match: str | Unset = UNSET,
    if_none_match: PutDocumentIfNoneMatch | Unset = UNSET,
    x_csrf_token: str | Unset = UNSET,
) -> Response[Error | MutationResult]:
    """Store one document

     Stores one document of at most 1 GiB. Content that is valid UTF-8 and at most 100 MiB is
    searchable. Any other content, such as an image or a larger file, is stored, listed, and served
    by the document endpoints but is never matched by a search. The `searchable` field of a listing
    reports which applies.

    Args:
        organization (str): An account or organization name. Accounts and organizations share one
            namespace. A name keeps the case it was created with, and any spelling that differs only
            in case refers to it; no other account or organization can take such a spelling.
        index (str): An index name, unique in its organization. A name keeps the case it was
            created with, and any spelling that differs only in case refers to it; no other index in
            the organization can take such a spelling.
        idempotency_key (str):
        if_match (str | Unset):
        if_none_match (PutDocumentIfNoneMatch | Unset):
        x_csrf_token (str | Unset):
        body (PutDocumentForm):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Error | MutationResult]
    """

    kwargs = _get_kwargs(
        organization=organization,
        index=index,
        body=body,
        idempotency_key=idempotency_key,
        if_match=if_match,
        if_none_match=if_none_match,
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
    body: PutDocumentForm,
    idempotency_key: str,
    if_match: str | Unset = UNSET,
    if_none_match: PutDocumentIfNoneMatch | Unset = UNSET,
    x_csrf_token: str | Unset = UNSET,
) -> Error | MutationResult | None:
    """Store one document

     Stores one document of at most 1 GiB. Content that is valid UTF-8 and at most 100 MiB is
    searchable. Any other content, such as an image or a larger file, is stored, listed, and served
    by the document endpoints but is never matched by a search. The `searchable` field of a listing
    reports which applies.

    Args:
        organization (str): An account or organization name. Accounts and organizations share one
            namespace. A name keeps the case it was created with, and any spelling that differs only
            in case refers to it; no other account or organization can take such a spelling.
        index (str): An index name, unique in its organization. A name keeps the case it was
            created with, and any spelling that differs only in case refers to it; no other index in
            the organization can take such a spelling.
        idempotency_key (str):
        if_match (str | Unset):
        if_none_match (PutDocumentIfNoneMatch | Unset):
        x_csrf_token (str | Unset):
        body (PutDocumentForm):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Error | MutationResult
    """

    return sync_detailed(
        organization=organization,
        index=index,
        client=client,
        body=body,
        idempotency_key=idempotency_key,
        if_match=if_match,
        if_none_match=if_none_match,
        x_csrf_token=x_csrf_token,
    ).parsed


async def asyncio_detailed(
    organization: str,
    index: str,
    *,
    client: AuthenticatedClient | Client,
    body: PutDocumentForm,
    idempotency_key: str,
    if_match: str | Unset = UNSET,
    if_none_match: PutDocumentIfNoneMatch | Unset = UNSET,
    x_csrf_token: str | Unset = UNSET,
) -> Response[Error | MutationResult]:
    """Store one document

     Stores one document of at most 1 GiB. Content that is valid UTF-8 and at most 100 MiB is
    searchable. Any other content, such as an image or a larger file, is stored, listed, and served
    by the document endpoints but is never matched by a search. The `searchable` field of a listing
    reports which applies.

    Args:
        organization (str): An account or organization name. Accounts and organizations share one
            namespace. A name keeps the case it was created with, and any spelling that differs only
            in case refers to it; no other account or organization can take such a spelling.
        index (str): An index name, unique in its organization. A name keeps the case it was
            created with, and any spelling that differs only in case refers to it; no other index in
            the organization can take such a spelling.
        idempotency_key (str):
        if_match (str | Unset):
        if_none_match (PutDocumentIfNoneMatch | Unset):
        x_csrf_token (str | Unset):
        body (PutDocumentForm):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Error | MutationResult]
    """

    kwargs = _get_kwargs(
        organization=organization,
        index=index,
        body=body,
        idempotency_key=idempotency_key,
        if_match=if_match,
        if_none_match=if_none_match,
        x_csrf_token=x_csrf_token,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    organization: str,
    index: str,
    *,
    client: AuthenticatedClient | Client,
    body: PutDocumentForm,
    idempotency_key: str,
    if_match: str | Unset = UNSET,
    if_none_match: PutDocumentIfNoneMatch | Unset = UNSET,
    x_csrf_token: str | Unset = UNSET,
) -> Error | MutationResult | None:
    """Store one document

     Stores one document of at most 1 GiB. Content that is valid UTF-8 and at most 100 MiB is
    searchable. Any other content, such as an image or a larger file, is stored, listed, and served
    by the document endpoints but is never matched by a search. The `searchable` field of a listing
    reports which applies.

    Args:
        organization (str): An account or organization name. Accounts and organizations share one
            namespace. A name keeps the case it was created with, and any spelling that differs only
            in case refers to it; no other account or organization can take such a spelling.
        index (str): An index name, unique in its organization. A name keeps the case it was
            created with, and any spelling that differs only in case refers to it; no other index in
            the organization can take such a spelling.
        idempotency_key (str):
        if_match (str | Unset):
        if_none_match (PutDocumentIfNoneMatch | Unset):
        x_csrf_token (str | Unset):
        body (PutDocumentForm):

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
            client=client,
            body=body,
            idempotency_key=idempotency_key,
            if_match=if_match,
            if_none_match=if_none_match,
            x_csrf_token=x_csrf_token,
        )
    ).parsed
