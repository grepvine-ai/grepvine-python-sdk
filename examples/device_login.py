"""Obtain an API key for this machine by approving a device login in the browser."""

import os
import socket

import grepvine
from grepvine.models import DeviceAuthorization


def show(authorization: DeviceAuthorization) -> None:
    print(f"Open {authorization.verification_uri_complete}")
    print(f"and check that it shows the code {authorization.user_code}")


def main() -> None:
    endpoint = os.environ.get("GREPVINE_API_ENDPOINT", "https://api.grepvine.ai")
    # Starting a device login needs no credentials.
    with grepvine.Client(endpoint=endpoint) as client:
        key = client.device_login.authorize(
            f"python-sdk on {socket.gethostname()}", on_code=show, timeout=600
        )
    print(f"Issued API key {key.prefix}... named {key.name!r}")
    with grepvine.Client(api_key=key.key, endpoint=endpoint) as client:
        print(f"Signed in as {client.account.me().name}")


if __name__ == "__main__":
    main()
