from http import HTTPStatus
from typing import Any, cast

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response

from ...models.device_approval_request import DeviceApprovalRequest
from ...models.error import Error


def _get_kwargs(
    *,
    body: DeviceApprovalRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/device/authorizations/approve",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Any | Error:
    if response.status_code == 204:
        response_204 = cast(Any, None)
        return response_204

    if response.status_code == 404:
        response_404 = Error.from_dict(response.json())

        return response_404

    response_default = Error.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[Any | Error]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: DeviceApprovalRequest,
) -> Response[Any | Error]:
    """Approve device authorization

     Approves a pending device authorization, identified by the code the device shows. The device's next
    poll receives a new API key with the name it asked for. Without a scope it grants what the device
    asked for; a scope replaces that as a whole, narrower or wider. The key never does more than the
    approving account can. A code that is unknown, already decided or expired is not found. Only a
    signed-in session can approve.

    Args:
        body (DeviceApprovalRequest): The device authorization to approve, and optionally the
            scope to grant.

    Raises:
        grepvine.APIError: The service answered with an error.
        grepvine.TransportError: The request could not be delivered.

    Returns:
        Response[Any | Error]
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
    body: DeviceApprovalRequest,
) -> Any | Error | None:
    """Approve device authorization

     Approves a pending device authorization, identified by the code the device shows. The device's next
    poll receives a new API key with the name it asked for. Without a scope it grants what the device
    asked for; a scope replaces that as a whole, narrower or wider. The key never does more than the
    approving account can. A code that is unknown, already decided or expired is not found. Only a
    signed-in session can approve.

    Args:
        body (DeviceApprovalRequest): The device authorization to approve, and optionally the
            scope to grant.

    Raises:
        grepvine.APIError: The service answered with an error.
        grepvine.TransportError: The request could not be delivered.

    Returns:
        Any | Error
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: DeviceApprovalRequest,
) -> Response[Any | Error]:
    """Approve device authorization

     Approves a pending device authorization, identified by the code the device shows. The device's next
    poll receives a new API key with the name it asked for. Without a scope it grants what the device
    asked for; a scope replaces that as a whole, narrower or wider. The key never does more than the
    approving account can. A code that is unknown, already decided or expired is not found. Only a
    signed-in session can approve.

    Args:
        body (DeviceApprovalRequest): The device authorization to approve, and optionally the
            scope to grant.

    Raises:
        grepvine.APIError: The service answered with an error.
        grepvine.TransportError: The request could not be delivered.

    Returns:
        Response[Any | Error]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: DeviceApprovalRequest,
) -> Any | Error | None:
    """Approve device authorization

     Approves a pending device authorization, identified by the code the device shows. The device's next
    poll receives a new API key with the name it asked for. Without a scope it grants what the device
    asked for; a scope replaces that as a whole, narrower or wider. The key never does more than the
    approving account can. A code that is unknown, already decided or expired is not found. Only a
    signed-in session can approve.

    Args:
        body (DeviceApprovalRequest): The device authorization to approve, and optionally the
            scope to grant.

    Raises:
        grepvine.APIError: The service answered with an error.
        grepvine.TransportError: The request could not be delivered.

    Returns:
        Any | Error
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
