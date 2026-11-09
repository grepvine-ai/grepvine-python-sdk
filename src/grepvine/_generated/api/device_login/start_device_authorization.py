from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response

from ...models.device_authorization import DeviceAuthorization
from ...models.device_authorization_request import DeviceAuthorizationRequest
from ...models.error import Error


def _get_kwargs(
    *,
    body: DeviceAuthorizationRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/device/authorizations",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> DeviceAuthorization | Error:
    if response.status_code == 200:
        response_200 = DeviceAuthorization.from_dict(response.json())

        return response_200

    response_default = Error.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[DeviceAuthorization | Error]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: DeviceAuthorizationRequest,
) -> Response[DeviceAuthorization | Error]:
    """Start device authorization

     Starts signing in a device, such as the command-line client, without entering a password on it. Show
    the user `user_code` and send them to `verification_uri` (or `verification_uri_complete`) to approve
    it in a signed-in browser, then poll for the API key with `device_code`. The authorization expires
    after `expires_in` seconds.

    Args:
        body (DeviceAuthorizationRequest): A request to sign in a device.

    Raises:
        grepvine.APIError: The service answered with an error.
        grepvine.TransportError: The request could not be delivered.

    Returns:
        Response[DeviceAuthorization | Error]
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
    body: DeviceAuthorizationRequest,
) -> DeviceAuthorization | Error | None:
    """Start device authorization

     Starts signing in a device, such as the command-line client, without entering a password on it. Show
    the user `user_code` and send them to `verification_uri` (or `verification_uri_complete`) to approve
    it in a signed-in browser, then poll for the API key with `device_code`. The authorization expires
    after `expires_in` seconds.

    Args:
        body (DeviceAuthorizationRequest): A request to sign in a device.

    Raises:
        grepvine.APIError: The service answered with an error.
        grepvine.TransportError: The request could not be delivered.

    Returns:
        DeviceAuthorization | Error
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: DeviceAuthorizationRequest,
) -> Response[DeviceAuthorization | Error]:
    """Start device authorization

     Starts signing in a device, such as the command-line client, without entering a password on it. Show
    the user `user_code` and send them to `verification_uri` (or `verification_uri_complete`) to approve
    it in a signed-in browser, then poll for the API key with `device_code`. The authorization expires
    after `expires_in` seconds.

    Args:
        body (DeviceAuthorizationRequest): A request to sign in a device.

    Raises:
        grepvine.APIError: The service answered with an error.
        grepvine.TransportError: The request could not be delivered.

    Returns:
        Response[DeviceAuthorization | Error]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: DeviceAuthorizationRequest,
) -> DeviceAuthorization | Error | None:
    """Start device authorization

     Starts signing in a device, such as the command-line client, without entering a password on it. Show
    the user `user_code` and send them to `verification_uri` (or `verification_uri_complete`) to approve
    it in a signed-in browser, then poll for the API key with `device_code`. The authorization expires
    after `expires_in` seconds.

    Args:
        body (DeviceAuthorizationRequest): A request to sign in a device.

    Raises:
        grepvine.APIError: The service answered with an error.
        grepvine.TransportError: The request could not be delivered.

    Returns:
        DeviceAuthorization | Error
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
