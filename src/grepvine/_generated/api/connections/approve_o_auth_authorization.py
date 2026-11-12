from http import HTTPStatus
from typing import Any

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response

from ...models.error import Error
from ...models.o_auth_approval_request import OAuthApprovalRequest
from ...models.o_auth_redirect import OAuthRedirect


def _get_kwargs(
    *,
    body: OAuthApprovalRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/oauth/authorizations/approve",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Error | OAuthRedirect:
    if response.status_code == 200:
        response_200 = OAuthRedirect.from_dict(response.json())

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
) -> Response[Error | OAuthRedirect]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: OAuthApprovalRequest,
) -> Response[Error | OAuthRedirect]:
    """Approve an app's sign-in request

     Approves an app's sign-in request with the scope the signed-in account chose, creating a connection,
    and returns the address to send the browser to, which hands the app a single-use code. The
    connection never does more than the approving account can, and expires after 90 days unless the app
    keeps using it. `manage_members` and `manage_organization` cannot be granted to an app. A 404 means
    the organization or an index named does not exist or is not visible. Only a signed-in session can
    approve.

    Args:
        body (OAuthApprovalRequest): The sign-in request to approve and the scope to grant it.

    Raises:
        grepvine.APIError: The service answered with an error.
        grepvine.TransportError: The request could not be delivered.

    Returns:
        Response[Error | OAuthRedirect]
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
    body: OAuthApprovalRequest,
) -> Error | OAuthRedirect | None:
    """Approve an app's sign-in request

     Approves an app's sign-in request with the scope the signed-in account chose, creating a connection,
    and returns the address to send the browser to, which hands the app a single-use code. The
    connection never does more than the approving account can, and expires after 90 days unless the app
    keeps using it. `manage_members` and `manage_organization` cannot be granted to an app. A 404 means
    the organization or an index named does not exist or is not visible. Only a signed-in session can
    approve.

    Args:
        body (OAuthApprovalRequest): The sign-in request to approve and the scope to grant it.

    Raises:
        grepvine.APIError: The service answered with an error.
        grepvine.TransportError: The request could not be delivered.

    Returns:
        Error | OAuthRedirect
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: OAuthApprovalRequest,
) -> Response[Error | OAuthRedirect]:
    """Approve an app's sign-in request

     Approves an app's sign-in request with the scope the signed-in account chose, creating a connection,
    and returns the address to send the browser to, which hands the app a single-use code. The
    connection never does more than the approving account can, and expires after 90 days unless the app
    keeps using it. `manage_members` and `manage_organization` cannot be granted to an app. A 404 means
    the organization or an index named does not exist or is not visible. Only a signed-in session can
    approve.

    Args:
        body (OAuthApprovalRequest): The sign-in request to approve and the scope to grant it.

    Raises:
        grepvine.APIError: The service answered with an error.
        grepvine.TransportError: The request could not be delivered.

    Returns:
        Response[Error | OAuthRedirect]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: OAuthApprovalRequest,
) -> Error | OAuthRedirect | None:
    """Approve an app's sign-in request

     Approves an app's sign-in request with the scope the signed-in account chose, creating a connection,
    and returns the address to send the browser to, which hands the app a single-use code. The
    connection never does more than the approving account can, and expires after 90 days unless the app
    keeps using it. `manage_members` and `manage_organization` cannot be granted to an app. A 404 means
    the organization or an index named does not exist or is not visible. Only a signed-in session can
    approve.

    Args:
        body (OAuthApprovalRequest): The sign-in request to approve and the scope to grant it.

    Raises:
        grepvine.APIError: The service answered with an error.
        grepvine.TransportError: The request could not be delivered.

    Returns:
        Error | OAuthRedirect
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
