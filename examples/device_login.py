"""Obtain an API key for this machine by approving a device login in the browser."""

import socket

import grepvine_sdk
from grepvine_sdk import DeviceAuthorization


def show(authorization: DeviceAuthorization) -> None:
    print(f"Open {authorization.verification_uri_complete}")
    print(f"and check that it shows the code {authorization.user_code}")


def main() -> None:
    # Starting a device login needs no credentials; only the endpoint is read.
    with grepvine_sdk.Client() as client:
        key = client.device_login.authorize(
            f"python-sdk on {socket.gethostname()}", on_code=show, timeout=600
        )
        print(f"Issued API key {key.prefix}... named {key.name!r}")
        client.configure(api_key=key.key)
        print(f"Signed in as {client.account.me().name}")


if __name__ == "__main__":
    main()
