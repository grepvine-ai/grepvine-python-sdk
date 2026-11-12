from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response

from ...models.device_decision_request import DeviceDecisionRequest
from ...models.error import Error
from ...models.pending_device_authorization import PendingDeviceAuthorization


def _get_kwargs(
    *,
    body: DeviceDecisionRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/device/authorizations/lookup",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Error | PendingDeviceAuthorization:
    if response.status_code == 200:
        response_200 = PendingDeviceAuthorization.from_dict(response.json())

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
) -> Response[Error | PendingDeviceAuthorization]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: DeviceDecisionRequest,
) -> Response[Error | PendingDeviceAuthorization]:
    """Read a pending device authorization

     Returns the scope a pending device authorization asks for. Only a signed-in session can read one.

    Args:
        body (DeviceDecisionRequest): The device authorization to approve or deny.

    Raises:
        grepvine.APIError: The service answered with an error.
        grepvine.TransportError: The request could not be delivered.

    Returns:
        Response[Error | PendingDeviceAuthorization]
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
    body: DeviceDecisionRequest,
) -> Error | PendingDeviceAuthorization | None:
    """Read a pending device authorization

     Returns the scope a pending device authorization asks for. Only a signed-in session can read one.

    Args:
        body (DeviceDecisionRequest): The device authorization to approve or deny.

    Raises:
        grepvine.APIError: The service answered with an error.
        grepvine.TransportError: The request could not be delivered.

    Returns:
        Error | PendingDeviceAuthorization
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: DeviceDecisionRequest,
) -> Response[Error | PendingDeviceAuthorization]:
    """Read a pending device authorization

     Returns the scope a pending device authorization asks for. Only a signed-in session can read one.

    Args:
        body (DeviceDecisionRequest): The device authorization to approve or deny.

    Raises:
        grepvine.APIError: The service answered with an error.
        grepvine.TransportError: The request could not be delivered.

    Returns:
        Response[Error | PendingDeviceAuthorization]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: DeviceDecisionRequest,
) -> Error | PendingDeviceAuthorization | None:
    """Read a pending device authorization

     Returns the scope a pending device authorization asks for. Only a signed-in session can read one.

    Args:
        body (DeviceDecisionRequest): The device authorization to approve or deny.

    Raises:
        grepvine.APIError: The service answered with an error.
        grepvine.TransportError: The request could not be delivered.

    Returns:
        Error | PendingDeviceAuthorization
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
