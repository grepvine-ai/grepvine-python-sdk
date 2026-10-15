"""Accounts, sessions, memberships, API keys and device login for the fake service.

The routes follow the public API: registration and sign-in start a session
(a cookie and a CSRF token that every state change must carry), reading the
current user rotates the CSRF token, and device login moves an authorization
from pending to approved or denied while the device polls.
"""

from __future__ import annotations

import re
import secrets
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any
from urllib.parse import unquote

import httpx

if TYPE_CHECKING:
    from tests.fake_server import FakeGrepvine

SESSION_COOKIE = "__Host-grepvine-session"
NAME = re.compile(r"^[A-Za-z][A-Za-z0-9-]{2,62}$")
ROLES = {"admin", "developer", "reader"}
OWNER = "alice"


def _stamp(moment: datetime) -> str:
    return moment.isoformat().replace("+00:00", "Z")


@dataclass
class FakeUser:
    id: str
    name: str
    email: str
    password: str
    created_at: str

    def to_json(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "created_at": self.created_at,
        }


@dataclass
class FakeKey:
    id: str
    name: str
    secret: str
    user: str
    created_at: str
    revoked_at: str | None = None

    def to_json(self) -> dict[str, Any]:
        body = {
            "id": self.id,
            "name": self.name,
            "prefix": self.secret[:12],
            "created_at": self.created_at,
        }
        if self.revoked_at:
            body["revoked_at"] = self.revoked_at
        return body


@dataclass
class FakeDevice:
    device_code: str
    user_code: str
    api_key_name: str
    status: str = "pending"
    user: str | None = None


@dataclass
class Principal:
    user: str
    session: str | None = None


@dataclass
class FakeAccounts:
    service: FakeGrepvine
    users: dict[str, FakeUser] = field(default_factory=dict)
    keys: list[FakeKey] = field(default_factory=list)
    sessions: dict[str, tuple[str, str]] = field(default_factory=dict)
    """Session cookie -> (user name, CSRF token)."""
    members: dict[str, dict[str, dict[str, Any]]] = field(default_factory=dict)
    """Organization -> user -> {"role", "created_at"}, both keys lower-cased."""
    devices: list[FakeDevice] = field(default_factory=list)
    device_interval: int = 5
    device_expires_in: int = 600
    slow_down_polls: int = 0
    """How many of the next device polls answer ``slow_down``."""
    polls: int = 0
    on_poll: Callable[[int], None] | None = None
    """Called with the number of device polls so far, before each one is answered."""

    def __post_init__(self) -> None:
        self.add_user(OWNER, "alice@example.com", "correct horse battery")

    # -- seeding -------------------------------------------------------------

    def add_user(self, name: str, email: str, password: str) -> FakeUser:
        user = FakeUser(str(uuid.uuid4()), name, email, password, _stamp(self.service.now))
        self.users[name.lower()] = user
        return user

    def add_member(self, organization: str, user: str, role: str) -> None:
        if user.lower() not in self.users:
            self.add_user(user, f"{user.lower()}@example.com", "a long enough password")
        self.members.setdefault(organization.lower(), {})[user.lower()] = {
            "role": role,
            "created_at": _stamp(self.service.now),
        }

    def device(self, user_code: str) -> FakeDevice:
        return next(device for device in self.devices if device.user_code == user_code)

    # -- authentication ------------------------------------------------------

    PUBLIC = {
        ("POST", "/auth/register"),
        ("POST", "/auth/login"),
        ("POST", "/device/authorizations"),
        ("POST", "/device/token"),
    }

    def is_public(self, method: str, path: str) -> bool:
        return (method, path) in self.PUBLIC or (
            method == "GET" and path.startswith("/auth/usernames/")
        )

    def authenticate(self, request: httpx.Request) -> Principal:
        from tests.fake_server import RejectError

        authorization = request.headers.get("Authorization")
        if authorization is not None:
            token = authorization.removeprefix("Bearer ")
            if token == self.service.api_key:
                return Principal(OWNER)
            for key in self.keys:
                if key.secret == token and key.revoked_at is None:
                    return Principal(key.user)
        else:
            cookies = dict(
                part.strip().partition("=")[::2]
                for part in request.headers.get("Cookie", "").split(";")
                if part.strip()
            )
            cookie = cookies.get(SESSION_COOKIE)
            if cookie is not None and cookie in self.sessions:
                user, csrf = self.sessions[cookie]
                if request.method != "GET" and request.headers.get("X-Csrf-Token") != csrf:
                    raise RejectError(
                        403, "csrf_failed", "the CSRF token is missing or invalid", reason="auth"
                    )
                return Principal(user, cookie)
        raise RejectError(
            401, "unauthenticated", "authentication is required", reason="authentication"
        )

    def _start_session(self, user: FakeUser, status: int) -> httpx.Response:
        cookie, csrf = secrets.token_hex(16), secrets.token_hex(16)
        self.sessions[cookie] = (user.name, csrf)
        return httpx.Response(
            status,
            json=user.to_json(),
            headers={
                "X-Csrf-Token": csrf,
                "Set-Cookie": f"{SESSION_COOKIE}={cookie}; Path=/; Secure; HttpOnly",
            },
        )

    # -- routing -------------------------------------------------------------

    def route(
        self, request: httpx.Request, method: str, path: str, principal: Principal | None
    ) -> httpx.Response | None:
        from tests.fake_server import RejectError

        service = self.service
        if (method, path) == ("POST", "/auth/register"):
            body = service._json(request)
            name = str(body.get("name", ""))
            if not NAME.match(name) or len(str(body.get("password", ""))) < 12:
                raise RejectError(400, "invalid_request", "the request is invalid")
            if name.lower() in self.users or name.lower() in service.organizations:
                raise RejectError(409, "username_taken", "the username is taken", reason="state")
            user = self.add_user(name, str(body["email"]), str(body["password"]))
            return self._start_session(user, 201)
        if (method, path) == ("POST", "/auth/login"):
            body = service._json(request)
            identifier = str(body.get("identifier", "")).lower()
            for user in self.users.values():
                if identifier in (
                    user.name.lower(),
                    user.email.lower(),
                ) and user.password == body.get("password"):
                    return self._start_session(user, 200)
            raise RejectError(
                401, "invalid_credentials", "the credentials are not valid", reason="authentication"
            )
        m = re.fullmatch(r"/auth/usernames/([^/]+)", path)
        if m and method == "GET":
            name = unquote(m.group(1))
            taken = name.lower() in self.users or name.lower() in service.organizations
            return httpx.Response(200, json={"name": name, "available": not taken})
        if (method, path) == ("POST", "/device/authorizations"):
            body = service._json(request)
            device = FakeDevice(
                secrets.token_hex(16), secrets.token_hex(4).upper(), body["api_key_name"]
            )
            self.devices.append(device)
            return httpx.Response(
                200,
                json={
                    "device_code": device.device_code,
                    "user_code": device.user_code,
                    "verification_uri": "https://grepvine.test/device",
                    "verification_uri_complete": f"https://grepvine.test/device?code={device.user_code}",
                    "expires_in": self.device_expires_in,
                    "interval": self.device_interval,
                },
            )
        if (method, path) == ("POST", "/device/token"):
            return self._poll(service._json(request))
        if principal is None:
            return None
        return self._authenticated(request, method, path, principal)

    def _poll(self, body: dict[str, Any]) -> httpx.Response:
        from tests.fake_server import RejectError

        self.polls += 1
        if self.on_poll is not None:
            self.on_poll(self.polls)
        device = next((d for d in self.devices if d.device_code == body.get("device_code")), None)

        def refuse(code: str, message: str) -> RejectError:
            return RejectError(400, code, message, reason="device_authorization")

        if device is None or device.status == "consumed":
            raise refuse("expired_token", "the device code is invalid or expired")
        if self.slow_down_polls:
            self.slow_down_polls -= 1
            raise refuse("slow_down", "polling is too frequent")
        if device.status == "pending":
            raise refuse("authorization_pending", "authorization is pending")
        if device.status == "denied":
            raise refuse("access_denied", "authorization was denied")
        device.status = "consumed"
        assert device.user is not None
        return httpx.Response(200, json=self._issue(device.api_key_name, device.user))

    def _issue(self, name: str, user: str) -> dict[str, Any]:
        key = FakeKey(
            str(uuid.uuid4()), name, "gvk_" + secrets.token_hex(20), user, _stamp(self.service.now)
        )
        self.keys.append(key)
        return {**key.to_json(), "key": key.secret}

    def _authenticated(
        self, request: httpx.Request, method: str, path: str, principal: Principal
    ) -> httpx.Response | None:
        from tests.fake_server import RejectError

        service = self.service
        if (method, path) == ("POST", "/auth/logout"):
            if principal.session is not None:
                del self.sessions[principal.session]
            return httpx.Response(
                204, headers={"Set-Cookie": f"{SESSION_COOKIE}=; Path=/; Max-Age=0"}
            )
        if (method, path) == ("GET", "/auth/me"):
            headers = {}
            if principal.session is not None:
                csrf = secrets.token_hex(16)
                self.sessions[principal.session] = (principal.user, csrf)
                headers["X-Csrf-Token"] = csrf
            return httpx.Response(
                200, json=self.users[principal.user.lower()].to_json(), headers=headers
            )
        if (method, path) == ("PUT", "/auth/password"):
            body = service._json(request)
            account = self.users[principal.user.lower()]
            if body.get("current_password") != account.password:
                raise RejectError(
                    401, "invalid_credentials", "the password is not valid", reason="authentication"
                )
            account.password = str(body["new_password"])
            return httpx.Response(204)
        if (method, path) in {
            ("POST", "/device/authorizations/approve"),
            ("POST", "/device/authorizations/deny"),
        }:
            code = service._json(request).get("user_code")
            device = next((d for d in self.devices if d.user_code == code), None)
            if device is None or device.status != "pending":
                raise RejectError(
                    404, "not_found", "the resource does not exist", reason="resource"
                )
            device.status = "approved" if path.endswith("approve") else "denied"
            device.user = principal.user
            return httpx.Response(204)
        if path == "/api-keys" and method == "GET":
            mine = [key.to_json() for key in self.keys if key.user == principal.user]
            return service._page(request, mine)
        if path == "/api-keys" and method == "POST":
            return httpx.Response(
                201, json=self._issue(service._json(request)["name"], principal.user)
            )
        m = re.fullmatch(r"/api-keys/([^/]+)", path)
        if m and method == "DELETE":
            for key in self.keys:
                if key.id == m.group(1) and key.user == principal.user:
                    key.revoked_at = _stamp(service.now)
                    return httpx.Response(204)
            raise RejectError(404, "not_found", "the resource does not exist", reason="resource")
        if path == "/organizations" and method == "POST":
            name = str(service._json(request).get("name", ""))
            if not NAME.match(name):
                raise RejectError(400, "invalid_name", "the name is invalid")
            if name.lower() in service.organizations or name.lower() in self.users:
                raise RejectError(409, "conflict", "the name is taken", reason="state")
            entry = service.add_organization(name)
            return httpx.Response(201, json=entry)
        m = re.fullmatch(r"/organizations/([^/]+)", path)
        if m and method == "DELETE":
            organization = service._organization(unquote(m.group(1)))
            del service.organizations[organization["name"].lower()]
            for index_key in [k for k in service.indexes if k[0] == organization["name"].lower()]:
                del service.indexes[index_key]
            return httpx.Response(202)
        m = re.fullmatch(r"/organizations/([^/]+)/owner", path)
        if m and method == "PUT":
            organization = service._organization(unquote(m.group(1)))
            members = self.members.setdefault(organization["name"].lower(), {})
            user = str(service._json(request).get("user", "")).lower()
            if user not in members:
                raise RejectError(404, "not_found", "the member does not exist", reason="resource")
            for entry in members.values():
                if entry["role"] == "owner":
                    entry["role"] = "admin"
            members[user]["role"] = "owner"
            return httpx.Response(204)
        m = re.fullmatch(r"/organizations/([^/]+)/members", path)
        if m:
            organization = service._organization(unquote(m.group(1)))
            members = self.members.setdefault(organization["name"].lower(), {})
            if method == "GET":
                return service._page(
                    request, [self._member(name, entry) for name, entry in sorted(members.items())]
                )
            if method == "POST":
                body = service._json(request)
                user = str(body.get("user", ""))
                if body.get("role") not in ROLES:
                    raise RejectError(400, "invalid_request", "the request is invalid")
                if user.lower() not in self.users:
                    raise RejectError(
                        404, "not_found", "the user does not exist", reason="resource"
                    )
                if user.lower() in members:
                    raise RejectError(409, "conflict", "the user is a member", reason="state")
                self.add_member(organization["name"], user, body["role"])
                return httpx.Response(201, json=self._member(user.lower(), members[user.lower()]))
        m = re.fullmatch(r"/organizations/([^/]+)/members/([^/]+)", path)
        if m:
            organization = service._organization(unquote(m.group(1)))
            members = self.members.setdefault(organization["name"].lower(), {})
            user = unquote(m.group(2)).lower()
            if user not in members:
                raise RejectError(404, "not_found", "the member does not exist", reason="resource")
            if method == "PUT":
                role = service._json(request).get("role")
                if role not in ROLES:
                    raise RejectError(400, "invalid_request", "the request is invalid")
                members[user]["role"] = role
                return httpx.Response(200, json=self._member(user, members[user]))
            if method == "DELETE":
                del members[user]
                return httpx.Response(204)
        return None

    def _member(self, user: str, entry: dict[str, Any]) -> dict[str, Any]:
        return {
            "user": self.users[user].to_json(),
            "role": entry["role"],
            "created_at": entry["created_at"],
        }
