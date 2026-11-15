from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response

from ...models.device_token import DeviceToken
from ...models.device_token_request import DeviceTokenRequest
from ...models.error import Error


def _get_kwargs(
    *,
    body: DeviceTokenRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/device/token",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> DeviceToken | Error:
    if response.status_code == 200:
        response_200 = DeviceToken.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = Error.from_dict(response.json())

        return response_400

    response_default = Error.from_dict(response.json())

    return response_default


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[DeviceToken | Error]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: DeviceTokenRequest,
) -> Response[DeviceToken | Error]:
    """Poll for a device API key

     Exchanges an approved device code for an API key, or for the agent secret it asked for, once. Until
    the user decides, a poll fails with 400 and code `authorization_pending`: poll again after
    `interval` seconds. Polling sooner fails with `slow_down` and adds 5 seconds to the interval. A
    denied authorization fails with `access_denied`, as does a request for a secret of an agent that
    already has two, and an unknown, expired or already used code with `expired_token`.

    Args:
        body (DeviceTokenRequest): The device code to exchange for an API key.

    Raises:
        grepvine.APIError: The service answered with an error.
        grepvine.TransportError: The request could not be delivered.

    Returns:
        Response[DeviceToken | Error]
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
    body: DeviceTokenRequest,
) -> DeviceToken | Error | None:
    """Poll for a device API key

     Exchanges an approved device code for an API key, or for the agent secret it asked for, once. Until
    the user decides, a poll fails with 400 and code `authorization_pending`: poll again after
    `interval` seconds. Polling sooner fails with `slow_down` and adds 5 seconds to the interval. A
    denied authorization fails with `access_denied`, as does a request for a secret of an agent that
    already has two, and an unknown, expired or already used code with `expired_token`.

    Args:
        body (DeviceTokenRequest): The device code to exchange for an API key.

    Raises:
        grepvine.APIError: The service answered with an error.
        grepvine.TransportError: The request could not be delivered.

    Returns:
        DeviceToken | Error
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: DeviceTokenRequest,
) -> Response[DeviceToken | Error]:
    """Poll for a device API key

     Exchanges an approved device code for an API key, or for the agent secret it asked for, once. Until
    the user decides, a poll fails with 400 and code `authorization_pending`: poll again after
    `interval` seconds. Polling sooner fails with `slow_down` and adds 5 seconds to the interval. A
    denied authorization fails with `access_denied`, as does a request for a secret of an agent that
    already has two, and an unknown, expired or already used code with `expired_token`.

    Args:
        body (DeviceTokenRequest): The device code to exchange for an API key.

    Raises:
        grepvine.APIError: The service answered with an error.
        grepvine.TransportError: The request could not be delivered.

    Returns:
        Response[DeviceToken | Error]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: DeviceTokenRequest,
) -> DeviceToken | Error | None:
    """Poll for a device API key

     Exchanges an approved device code for an API key, or for the agent secret it asked for, once. Until
    the user decides, a poll fails with 400 and code `authorization_pending`: poll again after
    `interval` seconds. Polling sooner fails with `slow_down` and adds 5 seconds to the interval. A
    denied authorization fails with `access_denied`, as does a request for a secret of an agent that
    already has two, and an unknown, expired or already used code with `expired_token`.

    Args:
        body (DeviceTokenRequest): The device code to exchange for an API key.

    Raises:
        grepvine.APIError: The service answered with an error.
        grepvine.TransportError: The request could not be delivered.

    Returns:
        DeviceToken | Error
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
