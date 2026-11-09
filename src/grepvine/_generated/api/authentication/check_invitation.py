from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response

from ...models.error import Error
from ...models.invitation_check_request import InvitationCheckRequest
from ...models.invitation_preview import InvitationPreview


def _get_kwargs(
    *,
    body: InvitationCheckRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/auth/invitations:check",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Error | InvitationPreview:
    if response.status_code == 200:
        response_200 = InvitationPreview.from_dict(response.json())

        return response_200

    if response.status_code == 404:
        response_404 = Error.from_dict(response.json())

        return response_404

    response_default = Error.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[Error | InvitationPreview]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: InvitationCheckRequest,
) -> Response[Error | InvitationPreview]:
    """Check an invitation

     Reports what a pending invitation offers, so the registration form can show it. The token travels in
    the body, never in the URL. An invitation that was used, withdrawn or has expired is not found.

    Args:
        body (InvitationCheckRequest): The invitation to look up.

    Raises:
        grepvine.APIError: The service answered with an error.
        grepvine.TransportError: The request could not be delivered.

    Returns:
        Response[Error | InvitationPreview]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    body: InvitationCheckRequest,
) -> Error | InvitationPreview | None:
    """Check an invitation

     Reports what a pending invitation offers, so the registration form can show it. The token travels in
    the body, never in the URL. An invitation that was used, withdrawn or has expired is not found.

    Args:
        body (InvitationCheckRequest): The invitation to look up.

    Raises:
        grepvine.APIError: The service answered with an error.
        grepvine.TransportError: The request could not be delivered.

    Returns:
        Error | InvitationPreview
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: InvitationCheckRequest,
) -> Response[Error | InvitationPreview]:
    """Check an invitation

     Reports what a pending invitation offers, so the registration form can show it. The token travels in
    the body, never in the URL. An invitation that was used, withdrawn or has expired is not found.

    Args:
        body (InvitationCheckRequest): The invitation to look up.

    Raises:
        grepvine.APIError: The service answered with an error.
        grepvine.TransportError: The request could not be delivered.

    Returns:
        Response[Error | InvitationPreview]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: InvitationCheckRequest,
) -> Error | InvitationPreview | None:
    """Check an invitation

     Reports what a pending invitation offers, so the registration form can show it. The token travels in
    the body, never in the URL. An invitation that was used, withdrawn or has expired is not found.

    Args:
        body (InvitationCheckRequest): The invitation to look up.

    Raises:
        grepvine.APIError: The service answered with an error.
        grepvine.TransportError: The request could not be delivered.

    Returns:
        Error | InvitationPreview
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
