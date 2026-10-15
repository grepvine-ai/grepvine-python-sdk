from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET

from ...models.error import Error
from ...models.mutation_batch_result import MutationBatchResult
from ...types import File
from ...types import Unset


def _get_kwargs(
    organization: str,
    index: str,
    *,
    body: File,
    idempotency_key: str,
    x_csrf_token: str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["Idempotency-Key"] = idempotency_key

    if not isinstance(x_csrf_token, Unset):
        headers["X-Csrf-Token"] = x_csrf_token

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/organizations/{organization}/indexes/{index}/objects:batch".format(
            organization=quote(str(organization), safe=""),
            index=quote(str(index), safe=""),
        ),
    }

    _kwargs["content"] = body.payload.read()
    headers["Content-Type"] = "application/x-ndjson"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Error | MutationBatchResult:
    if response.status_code == 200:
        response_200 = MutationBatchResult.from_dict(response.json())

        return response_200

    if response.status_code == 409:
        response_409 = Error.from_dict(response.json())

        return response_409

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
    body: File,
    idempotency_key: str,
    x_csrf_token: str | Unset = UNSET,
) -> Response[Error | MutationBatchResult]:
    """Store a batch of documents

     Stores up to 2,048 documents. Each document is stored on its own: a document whose precondition
    fails is not stored, the others are, and the result of each document says which happened. Retrying
    with the same Idempotency-Key returns the same results and stores any document an interrupted
    attempt did not reach. Batch content is text carried as JSON strings, so every document stored this
    way is searchable. Store binary content, or a document over 16 MiB, with the
    single-document endpoint. The body may be sent with `Content-Encoding: gzip`; the service decodes it
    before applying the limits below, and answers any other content encoding with 415
    `unsupported_content_encoding`.

    Args:
        organization (str): An account or organization name. Accounts and organizations share one
            namespace. A name keeps the case it was created with, and any spelling that differs only
            in case refers to it; no other account or organization can take such a spelling.
        index (str): An index name, unique in its organization. A name keeps the case it was
            created with, and any spelling that differs only in case refers to it; no other index in
            the organization can take such a spelling.
        idempotency_key (str):
        x_csrf_token (str | Unset):
        body (File): One PutObjectRecord JSON value per line; at most 2,048 records and 16 MiB of
            combined object content.

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
    body: File,
    idempotency_key: str,
    x_csrf_token: str | Unset = UNSET,
) -> Error | MutationBatchResult | None:
    """Store a batch of documents

     Stores up to 2,048 documents. Each document is stored on its own: a document whose precondition
    fails is not stored, the others are, and the result of each document says which happened. Retrying
    with the same Idempotency-Key returns the same results and stores any document an interrupted
    attempt did not reach. Batch content is text carried as JSON strings, so every document stored this
    way is searchable. Store binary content, or a document over 16 MiB, with the
    single-document endpoint. The body may be sent with `Content-Encoding: gzip`; the service decodes it
    before applying the limits below, and answers any other content encoding with 415
    `unsupported_content_encoding`.

    Args:
        organization (str): An account or organization name. Accounts and organizations share one
            namespace. A name keeps the case it was created with, and any spelling that differs only
            in case refers to it; no other account or organization can take such a spelling.
        index (str): An index name, unique in its organization. A name keeps the case it was
            created with, and any spelling that differs only in case refers to it; no other index in
            the organization can take such a spelling.
        idempotency_key (str):
        x_csrf_token (str | Unset):
        body (File): One PutObjectRecord JSON value per line; at most 2,048 records and 16 MiB of
            combined object content.

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
    body: File,
    idempotency_key: str,
    x_csrf_token: str | Unset = UNSET,
) -> Response[Error | MutationBatchResult]:
    """Store a batch of documents

     Stores up to 2,048 documents. Each document is stored on its own: a document whose precondition
    fails is not stored, the others are, and the result of each document says which happened. Retrying
    with the same Idempotency-Key returns the same results and stores any document an interrupted
    attempt did not reach. Batch content is text carried as JSON strings, so every document stored this
    way is searchable. Store binary content, or a document over 16 MiB, with the
    single-document endpoint. The body may be sent with `Content-Encoding: gzip`; the service decodes it
    before applying the limits below, and answers any other content encoding with 415
    `unsupported_content_encoding`.

    Args:
        organization (str): An account or organization name. Accounts and organizations share one
            namespace. A name keeps the case it was created with, and any spelling that differs only
            in case refers to it; no other account or organization can take such a spelling.
        index (str): An index name, unique in its organization. A name keeps the case it was
            created with, and any spelling that differs only in case refers to it; no other index in
            the organization can take such a spelling.
        idempotency_key (str):
        x_csrf_token (str | Unset):
        body (File): One PutObjectRecord JSON value per line; at most 2,048 records and 16 MiB of
            combined object content.

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
    body: File,
    idempotency_key: str,
    x_csrf_token: str | Unset = UNSET,
) -> Error | MutationBatchResult | None:
    """Store a batch of documents

     Stores up to 2,048 documents. Each document is stored on its own: a document whose precondition
    fails is not stored, the others are, and the result of each document says which happened. Retrying
    with the same Idempotency-Key returns the same results and stores any document an interrupted
    attempt did not reach. Batch content is text carried as JSON strings, so every document stored this
    way is searchable. Store binary content, or a document over 16 MiB, with the
    single-document endpoint. The body may be sent with `Content-Encoding: gzip`; the service decodes it
    before applying the limits below, and answers any other content encoding with 415
    `unsupported_content_encoding`.

    Args:
        organization (str): An account or organization name. Accounts and organizations share one
            namespace. A name keeps the case it was created with, and any spelling that differs only
            in case refers to it; no other account or organization can take such a spelling.
        index (str): An index name, unique in its organization. A name keeps the case it was
            created with, and any spelling that differs only in case refers to it; no other index in
            the organization can take such a spelling.
        idempotency_key (str):
        x_csrf_token (str | Unset):
        body (File): One PutObjectRecord JSON value per line; at most 2,048 records and 16 MiB of
            combined object content.

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
