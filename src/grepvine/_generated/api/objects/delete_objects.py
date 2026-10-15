from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET

from ...models.delete_objects_request import DeleteObjectsRequest
from ...models.error import Error
from ...models.mutation_batch_result import MutationBatchResult
from ...types import Unset


def _get_kwargs(
    organization: str,
    index: str,
    *,
    body: DeleteObjectsRequest,
    idempotency_key: str,
    x_csrf_token: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["Idempotency-Key"] = idempotency_key

    if not isinstance(x_csrf_token, Unset):
        headers["X-Csrf-Token"] = x_csrf_token

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/organizations/{organization}/indexes/{index}/objects:delete".format(
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
) -> Error | MutationBatchResult:
    if response.status_code == 200:
        response_200 = MutationBatchResult.from_dict(response.json())

        return response_200

    response_default = Error.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[Error | MutationBatchResult]:
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
    body: DeleteObjectsRequest,
    idempotency_key: str,
    x_csrf_token: str | Unset = UNSET,
) -> Response[Error | MutationBatchResult]:
    """Delete a batch of documents

     Deletes up to 2,048 documents. Each document is deleted on its own: a document that does not
    exist or whose precondition fails is not deleted, the others are, and the result of each document
    says which happened. Retrying with the same Idempotency-Key returns the same results.

    Args:
        organization (str): An account or organization name. Accounts and organizations share one
            namespace. A name keeps the case it was created with, and any spelling that differs only
            in case refers to it; no other account or organization can take such a spelling.
        index (str): An index name, unique in its organization. A name keeps the case it was
            created with, and any spelling that differs only in case refers to it; no other index in
            the organization can take such a spelling.
        idempotency_key (str):
        x_csrf_token (str | Unset):
        body (DeleteObjectsRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Error | MutationBatchResult]
    """

    kwargs = _get_kwargs(
        organization=organization,
        index=index,
        body=body,
        idempotency_key=idempotency_key,
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
    body: DeleteObjectsRequest,
    idempotency_key: str,
    x_csrf_token: str | Unset = UNSET,
) -> Error | MutationBatchResult | None:
    """Delete a batch of documents

     Deletes up to 2,048 documents. Each document is deleted on its own: a document that does not
    exist or whose precondition fails is not deleted, the others are, and the result of each document
    says which happened. Retrying with the same Idempotency-Key returns the same results.

    Args:
        organization (str): An account or organization name. Accounts and organizations share one
            namespace. A name keeps the case it was created with, and any spelling that differs only
            in case refers to it; no other account or organization can take such a spelling.
        index (str): An index name, unique in its organization. A name keeps the case it was
            created with, and any spelling that differs only in case refers to it; no other index in
            the organization can take such a spelling.
        idempotency_key (str):
        x_csrf_token (str | Unset):
        body (DeleteObjectsRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Error | MutationBatchResult
    """

    return sync_detailed(
        organization=organization,
        index=index,
        client=client,
        body=body,
        idempotency_key=idempotency_key,
        x_csrf_token=x_csrf_token,
    ).parsed


async def asyncio_detailed(
    organization: str,
    index: str,
    *,
    client: AuthenticatedClient | Client,
    body: DeleteObjectsRequest,
    idempotency_key: str,
    x_csrf_token: str | Unset = UNSET,
) -> Response[Error | MutationBatchResult]:
    """Delete a batch of documents

     Deletes up to 2,048 documents. Each document is deleted on its own: a document that does not
    exist or whose precondition fails is not deleted, the others are, and the result of each document
    says which happened. Retrying with the same Idempotency-Key returns the same results.

    Args:
        organization (str): An account or organization name. Accounts and organizations share one
            namespace. A name keeps the case it was created with, and any spelling that differs only
            in case refers to it; no other account or organization can take such a spelling.
        index (str): An index name, unique in its organization. A name keeps the case it was
            created with, and any spelling that differs only in case refers to it; no other index in
            the organization can take such a spelling.
        idempotency_key (str):
        x_csrf_token (str | Unset):
        body (DeleteObjectsRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Error | MutationBatchResult]
    """

    kwargs = _get_kwargs(
        organization=organization,
        index=index,
        body=body,
        idempotency_key=idempotency_key,
        x_csrf_token=x_csrf_token,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    organization: str,
    index: str,
    *,
    client: AuthenticatedClient | Client,
    body: DeleteObjectsRequest,
    idempotency_key: str,
    x_csrf_token: str | Unset = UNSET,
) -> Error | MutationBatchResult | None:
    """Delete a batch of documents

     Deletes up to 2,048 documents. Each document is deleted on its own: a document that does not
    exist or whose precondition fails is not deleted, the others are, and the result of each document
    says which happened. Retrying with the same Idempotency-Key returns the same results.

    Args:
        organization (str): An account or organization name. Accounts and organizations share one
            namespace. A name keeps the case it was created with, and any spelling that differs only
            in case refers to it; no other account or organization can take such a spelling.
        index (str): An index name, unique in its organization. A name keeps the case it was
            created with, and any spelling that differs only in case refers to it; no other index in
            the organization can take such a spelling.
        idempotency_key (str):
        x_csrf_token (str | Unset):
        body (DeleteObjectsRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Error | MutationBatchResult
    """

    return (
        await asyncio_detailed(
            organization=organization,
            index=index,
            client=client,
            body=body,
            idempotency_key=idempotency_key,
            x_csrf_token=x_csrf_token,
        )
    ).parsed
