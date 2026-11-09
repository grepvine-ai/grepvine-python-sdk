"""An in-memory Grepvine service for running the README and examples end to end.

It keeps organizations, members, indexes, documents, API keys and accounts, and enforces the
rules a sample can get wrong: a name must exist, ownership goes to a member, only the owner deletes
an organization, an index is `creating` before it is `ready` and `deleting` before it is gone, and
conditional writes check revisions. Search supports regex and literal patterns, case and whole-word
options, context lines and a small filter language (`=`, `!=`, `<`, `<=`, `>`, `>=`, `STARTSWITH`,
joined by `AND`).
"""

from __future__ import annotations

import json
import operator
import re
import uuid
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import unquote

import httpx

NOW = "2026-01-01T00:00:00Z"
PASSWORD = "a long passphrase"


class Refused(Exception):
    def __init__(self, status: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status, self.code, self.message = status, code, message


@dataclass
class Document:
    key: str
    content: bytes
    metadata: dict[str, dict[str, Any]]
    revision: str = field(default_factory=lambda: uuid.uuid4().hex[:12])

    def summary(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "revision": self.revision,
            "content_bytes": len(self.content),
            "metadata": self.metadata,
            "updated_at": NOW,
            "searchable": _is_text(self.content),
        }


@dataclass
class Index:
    organization: str
    name: str
    description: str = ""
    tags: dict[str, str] = field(default_factory=dict)
    state: str = "ready"
    documents: dict[str, Document] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def json(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organization": self.organization,
            "name": self.name,
            "canonical_id": self.id,
            "description": self.description,
            "tags": self.tags,
            "state": self.state,
            "document_count": len(self.documents),
            "content_bytes": sum(len(d.content) for d in self.documents.values()),
            "created_at": NOW,
        }


@dataclass
class Organization:
    name: str
    members: dict[str, str]
    indexes: dict[str, Index] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))


def _is_text(content: bytes) -> bool:
    try:
        content.decode("utf-8")
    except UnicodeDecodeError:
        return False
    return True


def _tagged(value: Any) -> dict[str, Any]:
    if isinstance(value, dict) and "type" in value:
        return value
    for kind, tag in ((bool, "boolean"), (int, "integer"), (float, "number"), (str, "string")):
        if isinstance(value, kind):
            return {"type": tag, "value": value}
    raise Refused(400, "invalid_metadata", "a metadata value has an unsupported type")


def _page(items: list[Any], request: httpx.Request) -> tuple[list[Any], dict[str, Any]]:
    amount = int(request.url.params.get("amount", "50"))
    if not 1 <= amount <= 200:
        raise Refused(400, "invalid_argument", "amount must be between 1 and 200")
    start = int(request.url.params.get("page") or 0)
    chunk = items[start : start + amount]
    more = start + amount < len(items)
    return chunk, {"next_page_id": str(start + amount) if more else "", "has_next": more}


_CONDITION = re.compile(
    r"^\s*(\w+)\s*(STARTSWITH|!=|<=|>=|=|<|>)\s*('(?:[^']|'')*'|-?\d+(?:\.\d+)?)\s*$", re.I
)


_OPERATORS = {
    "STARTSWITH": lambda actual, expected: str(actual).startswith(str(expected)),
    "=": operator.eq,
    "!=": operator.ne,
    "<": operator.lt,
    "<=": operator.le,
    ">": operator.gt,
    ">=": operator.ge,
}


def _matches_filter(document: Document, expression: str | None) -> bool:
    if not expression:
        return True
    for condition in re.split(r"\s+AND\s+", expression, flags=re.I):
        found = _CONDITION.match(condition)
        if not found:
            raise Refused(400, "invalid_filter", f"the filter cannot be read: {condition!r}")
        name, comparison, raw = found.groups()
        expected: Any = raw[1:-1].replace("''", "'") if raw.startswith("'") else float(raw)
        actual = document.metadata.get(name, {}).get("value")
        if actual is None:
            return False
        if isinstance(expected, float) and not isinstance(actual, int | float):
            return False
        compare = _OPERATORS[comparison.upper()]
        result = compare(actual, expected)
        if not result:
            return False
    return True


class FakeGrepvine:
    """Answers the Grepvine API from memory; `handle` is an httpx.MockTransport handler."""

    def __init__(self) -> None:
        self.users = {
            name: {"id": str(uuid.uuid4()), "email": f"{name}@example.com", "password": PASSWORD}
            for name in ("alice", "bob", "carol")
        }
        self.keys: dict[str, dict[str, Any]] = {}
        self.sessions: dict[str, str] = {}
        self.devices: dict[str, dict[str, Any]] = {}
        self.orgs: dict[str, Organization] = {}
        self.requests: list[httpx.Request] = []
        self.api_key = self.issue_key("alice", "test")["key"]
        self.orgs["acme"] = Organization("acme", {"alice": "owner"})

    # Setup helpers for tests.

    def issue_key(self, user: str, name: str) -> dict[str, Any]:
        secret = f"gvk_{uuid.uuid4().hex}"
        record = {
            "id": str(uuid.uuid4()),
            "name": name,
            "prefix": secret[:8],
            "created_at": NOW,
            "user": user,
            "key": secret,
        }
        self.keys[secret] = record
        return record

    def add_index(
        self, organization: str, name: str, documents: dict[str, str] | None = None
    ) -> Index:
        index = Index(organization, name)
        self.orgs[organization].indexes[name] = index
        for key, text in (documents or {}).items():
            content = text.encode()
            index.documents[key] = Document(
                key, content, {"path": _tagged(key), "size": _tagged(len(content))}
            )
        return index

    # Request handling.

    def handle(self, request: httpx.Request) -> httpx.Response:
        request.read()
        self.requests.append(request)
        try:
            status, body = self.route(request)
        except Refused as refused:
            payload = {"code": refused.code, "reason": "fake", "error": refused.message}
            return httpx.Response(refused.status, json=payload)
        if isinstance(body, bytes):
            return httpx.Response(status, content=body)
        if body is None:
            return httpx.Response(status)
        headers = {}
        if request.url.path.endswith("/auth/login"):
            headers = {"Set-Cookie": "__Host-grepvine-session=s; Path=/", "X-Csrf-Token": "csrf"}
        return httpx.Response(status, json=body, headers=headers)

    def user(self, request: httpx.Request) -> str:
        token = request.headers.get("Authorization", "").removeprefix("Bearer ")
        if token in self.keys and "revoked_at" not in self.keys[token]:
            return str(self.keys[token]["user"])
        cookie = request.headers.get("Cookie", "")
        if "grepvine-session=s" in cookie and self.sessions.get("s"):
            return self.sessions["s"]
        raise Refused(401, "unauthenticated", "sign in or pass an API key")

    def org(self, name: str, user: str, roles: tuple[str, ...] = ()) -> Organization:
        org = self.orgs.get(name)
        if org is None or user not in org.members:
            raise Refused(404, "not_found", f"organization {name} does not exist")
        if roles and org.members[user] not in roles:
            raise Refused(403, "permission_denied", "your role does not allow this")
        return org

    def index(self, org: Organization, name: str) -> Index:
        index = org.indexes.get(name)
        if index is None:
            raise Refused(404, "not_found", f"index {org.name}/{name} does not exist")
        return index

    def route(self, request: httpx.Request) -> tuple[int, Any]:
        path = request.url.raw_path.decode().split("?")[0].removeprefix("/v1")
        method = request.method
        body: Any = None
        if request.headers.get("content-type", "").startswith("application/json"):
            body = json.loads(request.content or b"null")
        parts = [unquote(part) for part in path.strip("/").split("/")]
        if parts[0] == "auth":
            return self.auth(method, parts[1:], body, request)
        if parts[0] == "device":
            return self.device(parts[1:], body, request)
        user = self.user(request)
        if parts[0] == "api-keys":
            return self.api_keys(method, parts[1:], body, request, user)
        if parts[0] == "organizations":
            return self.organizations(method, parts[1:], body, request, user)
        raise Refused(404, "not_found", f"no route {method} {path}")

    def auth(
        self, method: str, parts: list[str], body: Any, request: httpx.Request
    ) -> tuple[int, Any]:
        def user_json(name: str) -> dict[str, Any]:
            record = self.users[name]
            return {"id": record["id"], "name": name, "email": record["email"], "created_at": NOW}

        match parts:
            case ["options"]:
                return 200, {"signup": "open"}
            case ["usernames", name]:
                return 200, {
                    "name": name,
                    "available": name not in self.users and name not in self.orgs,
                }
            case ["register"]:
                if body["name"] in self.users:
                    raise Refused(409, "username_taken", "that username is taken")
                if len(body["password"]) < 12:
                    raise Refused(400, "invalid_argument", "passwords are at least 12 characters")
                self.users[body["name"]] = {
                    "id": str(uuid.uuid4()),
                    "email": body["email"],
                    "password": body["password"],
                }
                return 201, user_json(body["name"])
            case ["login"]:
                record = self.users.get(body["identifier"])
                if record is None or record["password"] != body["password"]:
                    raise Refused(401, "unauthenticated", "wrong username or password")
                self.sessions["s"] = body["identifier"]
                return 200, user_json(body["identifier"])
            case ["logout"]:
                self.sessions.pop("s", None)
                return 204, None
            case ["me"]:
                return 200, user_json(self.user(request))
            case ["password"]:
                name = self.user(request)
                if self.users[name]["password"] != body["current_password"]:
                    raise Refused(401, "unauthenticated", "the current password is wrong")
                self.users[name]["password"] = body["new_password"]
                return 204, None
            case ["invitations:check"]:
                return 200, {"email": "new@example.com", "expires_at": NOW}
        raise Refused(404, "not_found", "no such route")

    def device(self, parts: list[str], body: Any, request: httpx.Request) -> tuple[int, Any]:
        match parts:
            case ["authorizations"]:
                code = uuid.uuid4().hex
                user_code = code[:4].upper() + "-" + code[4:8].upper()
                self.devices[code] = {
                    "name": body["api_key_name"],
                    "user_code": user_code,
                    "polls": 0,
                }
                return 200, {
                    "device_code": code,
                    "user_code": user_code,
                    "verification_uri": "https://console.example/device",
                    "verification_uri_complete": f"https://console.example/device?code={user_code}",
                    "expires_in": 600,
                    "interval": 5,
                }
            case ["authorizations", "approve" | "deny" as decision]:
                self.user(request)
                for device in self.devices.values():
                    if device["user_code"] == body["user_code"]:
                        device["decision"] = decision
                        return 204, None
                raise Refused(404, "not_found", "no such code")
            case ["token"]:
                device = self.devices[body["device_code"]]
                device["polls"] += 1
                # A person approves on the second poll unless a test decided otherwise.
                if device.get("decision", "approve" if device["polls"] > 1 else None) is None:
                    raise Refused(400, "authorization_pending", "not approved yet")
                if device.get("decision") == "deny":
                    raise Refused(400, "access_denied", "the login was denied")
                record = self.issue_key("alice", device["name"])
                return 200, {k: v for k, v in record.items() if k != "user"}
        raise Refused(404, "not_found", "no such route")

    def api_keys(
        self, method: str, parts: list[str], body: Any, request: httpx.Request, user: str
    ) -> tuple[int, Any]:
        public = ("id", "name", "prefix", "created_at", "last_used_at", "revoked_at")
        if method == "POST":
            record = self.issue_key(user, body["name"])
            return 201, {k: v for k, v in record.items() if k != "user"}
        if method == "GET":
            mine = [
                {k: v for k, v in r.items() if k in public}
                for r in self.keys.values()
                if r["user"] == user
            ]
            items, pagination = _page(mine, request)
            return 200, {"results": items, "pagination": pagination}
        for record in self.keys.values():
            if record["id"] == parts[0] and record["user"] == user:
                record["revoked_at"] = NOW
                return 204, None
        raise Refused(404, "not_found", "no such API key")

    def organizations(
        self, method: str, parts: list[str], body: Any, request: httpx.Request, user: str
    ) -> tuple[int, Any]:
        def org_json(org: Organization) -> dict[str, Any]:
            return {
                "id": org.id,
                "name": org.name,
                "role": org.members[user],
                "suspended": False,
                "created_at": NOW,
            }

        if not parts:
            if method == "POST":
                if body["name"] in self.orgs or body["name"] in self.users:
                    raise Refused(409, "conflict", "that name is taken")
                self.orgs[body["name"]] = Organization(body["name"], {user: "owner"})
                return 201, org_json(self.orgs[body["name"]])
            mine = [org_json(o) for o in self.orgs.values() if user in o.members]
            items, pagination = _page(mine, request)
            return 200, {"results": items, "pagination": pagination}
        name, rest = parts[0], parts[1:]
        if not rest:
            if method == "DELETE":
                self.org(name, user, ("owner",))
                del self.orgs[name]
                return 202, None
            return 200, org_json(self.org(name, user))
        if rest[0] == "owner":
            org = self.org(name, user, ("owner",))
            if body["user"] not in org.members:
                raise Refused(404, "not_found", f"{body['user']} is not a member of {name}")
            org.members[user] = "admin"
            org.members[body["user"]] = "owner"
            return 204, None
        if rest[0] == "members":
            return self.members(method, rest[1:], body, request, self.org(name, user), user)
        return self.indexes(method, rest[1:], body, request, self.org(name, user))

    def members(
        self,
        method: str,
        rest: list[str],
        body: Any,
        request: httpx.Request,
        org: Organization,
        user: str,
    ) -> tuple[int, Any]:
        def member_json(name: str) -> dict[str, Any]:
            record = self.users[name]
            user_json = {
                "id": record["id"],
                "name": name,
                "email": record["email"],
                "created_at": NOW,
            }
            return {"user": user_json, "role": org.members[name], "created_at": NOW}

        if method == "GET":
            items, pagination = _page([member_json(n) for n in org.members], request)
            return 200, {"results": items, "pagination": pagination}
        if org.members[user] not in ("owner", "admin"):
            raise Refused(403, "permission_denied", "your role does not allow this")
        if method == "POST":
            if body["user"] not in self.users:
                raise Refused(404, "not_found", f"user {body['user']} does not exist")
            org.members[body["user"]] = body["role"]
            return 201, member_json(body["user"])
        if rest[0] not in org.members:
            raise Refused(404, "not_found", f"{rest[0]} is not a member of {org.name}")
        if method == "PUT":
            org.members[rest[0]] = body["role"]
            return 200, member_json(rest[0])
        del org.members[rest[0]]
        return 204, None

    def indexes(
        self, method: str, rest: list[str], body: Any, request: httpx.Request, org: Organization
    ) -> tuple[int, Any]:
        if not rest:
            if method == "POST":
                if body["name"] in org.indexes:
                    raise Refused(409, "conflict", f"index {org.name}/{body['name']} exists")
                index = Index(org.name, body["name"], body.get("description", ""))
                index.tags = dict(body.get("tags") or {})
                index.state = "creating"
                org.indexes[body["name"]] = index
                return 201, index.json()
            prefix = request.url.params.get("prefix", "")
            found = [i.json() for n, i in sorted(org.indexes.items()) if n.startswith(prefix)]
            items, pagination = _page(found, request)
            return 200, {"results": items, "pagination": pagination}
        index = self.index(org, rest[0])
        tail = rest[1:]
        if not tail:
            return self.one_index(method, body, org, index)
        if tail[0] == "query":
            return self.query(body, request, index)
        if tail[0] == "objects:batch":
            return self.put_batch(request, index)
        if tail[0] == "objects:delete":
            results = [
                self.delete_document(index, record["key"], record.get("if_match"))
                for record in body["objects"]
            ]
            return 200, {"results": results}
        if tail[0] == "objects" and len(tail) == 1:
            if method == "PUT":
                return self.put_document(request, index)
            return self.list_documents(request, index)
        key = "/".join(tail[1:])
        if method == "DELETE":
            result = self.delete_document(index, key, request.headers.get("If-Match"))
            if "error" in result:
                raise Refused(412, "precondition_failed", "the revision does not match")
            return 200, result
        return self.get_document(request, index, key)

    def one_index(self, method: str, body: Any, org: Organization, index: Index) -> tuple[int, Any]:
        if method == "DELETE":
            index.state = "deleting"
            return 202, None
        if method == "PATCH":
            if "description" in body:
                index.description = body["description"]
            for name, value in (body.get("tags") or {}).items():
                if value is None:
                    index.tags.pop(name, None)
                else:
                    index.tags[name] = value
            return 200, index.json()
        answer = index.json()
        # The background work finishes after one read: creating becomes ready, deleting gone.
        if index.state == "creating":
            index.state = "ready"
        elif index.state == "deleting":
            del org.indexes[index.name]
        return 200, answer

    def store(
        self,
        index: Index,
        key: str,
        content: bytes,
        metadata: dict[str, Any],
        if_match: str | None,
        if_none_match: bool,
    ) -> dict[str, Any]:
        current = index.documents.get(key)
        if (if_none_match and current) or (
            if_match and (not current or current.revision != if_match)
        ):
            return {
                "key": key,
                "error": {
                    "code": "precondition_failed",
                    "reason": "fake",
                    "error": "the condition failed",
                },
            }
        tagged = {"path": _tagged(key), "size": _tagged(len(content))}
        tagged.update({name: _tagged(value) for name, value in metadata.items()})
        document = Document(key, content, tagged)
        index.documents[key] = document
        return {"key": key, "revision": document.revision}

    def put_document(self, request: httpx.Request, index: Index) -> tuple[int, Any]:
        boundary = request.headers["content-type"].split("boundary=")[1].encode()
        fields: dict[str, bytes] = {}
        for part in request.content.split(b"--" + boundary)[1:-1]:
            head, _, value = part.strip(b"\r\n").partition(b"\r\n\r\n")
            name = re.search(rb'name="([^"]+)"', head)
            assert name, head
            fields[name.group(1).decode()] = value
        metadata = json.loads(fields["metadata"]) if "metadata" in fields else {}
        result = self.store(
            index,
            fields["key"].decode(),
            fields["content"],
            metadata,
            request.headers.get("If-Match"),
            request.headers.get("If-None-Match") == "*",
        )
        if "error" in result:
            raise Refused(412, "precondition_failed", "the condition failed")
        return 200, result

    def put_batch(self, request: httpx.Request, index: Index) -> tuple[int, Any]:
        results = []
        for line in request.content.splitlines():
            record = json.loads(line)
            results.append(
                self.store(
                    index,
                    record["key"],
                    record["content"].encode(),
                    record.get("metadata", {}),
                    record.get("if_match"),
                    record.get("if_none_match") == "*",
                )
            )
        return 200, {"results": results}

    def delete_document(self, index: Index, key: str, if_match: str | None) -> dict[str, Any]:
        current = index.documents.get(key)
        if if_match and (current is None or current.revision != if_match):
            return {
                "key": key,
                "error": {"code": "precondition_failed", "reason": "fake", "error": "no"},
            }
        index.documents.pop(key, None)
        return {"key": key}

    def list_documents(self, request: httpx.Request, index: Index) -> tuple[int, Any]:
        prefix = request.url.params.get("prefix", "")
        delimiter = request.url.params.get("delimiter")
        documents, prefixes = [], []
        for key in sorted(index.documents):
            if not key.startswith(prefix):
                continue
            rest = key[len(prefix) :]
            if delimiter and delimiter in rest:
                folded = prefix + rest.split(delimiter)[0] + delimiter
                if folded not in prefixes:
                    prefixes.append(folded)
                continue
            documents.append(index.documents[key].summary())
        items, pagination = _page(documents, request)
        return 200, {"results": items, "common_prefixes": prefixes, "pagination": pagination}

    def get_document(self, request: httpx.Request, index: Index, key: str) -> tuple[int, Any]:
        document = index.documents.get(key)
        if document is None:
            raise Refused(404, "not_found", f"document {key} does not exist")
        byte_range = request.headers.get("Range")
        if byte_range:
            start, _, end = byte_range.removeprefix("bytes=").partition("-")
            first = int(start)
            if first >= len(document.content):
                raise Refused(416, "range_not_satisfiable", "the range is past the end")
            return 206, document.content[first : int(end) + 1 if end else None]
        return 200, document.content

    def query(self, body: dict[str, Any], request: httpx.Request, index: Index) -> tuple[int, Any]:
        pattern = body["pattern"]
        if body.get("mode") == "literal":
            pattern = re.escape(pattern)
            if body.get("whole_word"):
                pattern = rf"\b{pattern}\b"
        flags = 0 if body.get("case_sensitive", True) else re.IGNORECASE
        try:
            compiled = re.compile(pattern, flags)
        except re.error as error:
            raise Refused(400, "invalid_pattern", f"the pattern cannot be read: {error}") from None
        before, after = body.get("lines_before", 0), body.get("lines_after", 0)
        hits = []
        for key in sorted(index.documents):
            document = index.documents[key]
            if not document.summary()["searchable"] or not _matches_filter(
                document, body.get("filter")
            ):
                continue
            lines = document.content.decode().splitlines()
            offset = 0
            for number, text in enumerate(lines, start=1):
                found = [m for m in compiled.finditer(text)]
                if found:
                    hits.append(
                        {
                            "key": key,
                            "revision": document.revision,
                            "line_number": number,
                            "last_line_number": number,
                            "line_start_offset": offset,
                            "line_end_offset": offset + len(text.encode()),
                            "text_start_offset": offset,
                            "text_line_number": number,
                            "text": text,
                            "matches": [
                                {"offset": offset + m.start(), "length": len(m.group(0).encode())}
                                for m in found
                            ],
                            "text_truncated": False,
                            "matches_truncated": False,
                            **(
                                {
                                    "lines_before": [
                                        {
                                            "line_number": n,
                                            "text": lines[n - 1],
                                            "text_truncated": False,
                                        }
                                        for n in range(max(1, number - before), number)
                                    ]
                                }
                                if before
                                else {}
                            ),
                            **(
                                {
                                    "lines_after": [
                                        {
                                            "line_number": n,
                                            "text": lines[n - 1],
                                            "text_truncated": False,
                                        }
                                        for n in range(
                                            number + 1, min(len(lines), number + after) + 1
                                        )
                                    ]
                                }
                                if after
                                else {}
                            ),
                        }
                    )
                offset += len(text.encode()) + 1
        items, pagination = _page(hits, request)
        return 200, {"results": items, "pagination": pagination}
