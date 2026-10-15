"""An in-memory Grepvine service for tests, served through ``httpx.MockTransport``.

It speaks the public API's wire shapes closely enough to exercise the SDK end
to end without a network: bearer authentication, every route the SDK uses,
idempotency replay, preconditions, per-document batch results, byte ranges,
folded listings, regex search with byte offsets, and page tokens bound to the
request's arguments.
"""

from __future__ import annotations

import base64
import email
import email.policy
import hashlib
import json
import re
import unicodedata
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import unquote

import httpx

API_KEY = "gvk_test-key-0123456789abcdefghijklmnop"
# Names keep their case and are looked up without regard to it, so both registries are keyed by the
# lowercased name.
ORG_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9-]{2,62}$")
INDEX_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9-]{0,62}$")
MAX_BATCH_RECORDS = 2048
MAX_BATCH_BYTES = 16 * 1024 * 1024
MAX_AMOUNT = 200
MAX_TAGS = 64
MAX_TAG_KEY_LENGTH = 128
MAX_TAG_VALUE_LENGTH = 1024
TOKEN_TTL = timedelta(minutes=15)


class RejectError(Exception):
    """Abort request handling with an API error."""

    def __init__(
        self,
        status: int,
        code: str,
        message: str,
        *,
        reason: str = "validation",
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(message)
        self.status = status
        self.code = code
        self.reason = reason
        self.message = message
        self.headers = headers or {}


@dataclass
class StoredDocument:
    key: str
    content: bytes
    metadata: dict[str, Any]
    revision: str
    updated_at: datetime

    @property
    def searchable(self) -> bool:
        try:
            self.content.decode("utf-8")
        except UnicodeDecodeError:
            return False
        return True

    def summary(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "revision": self.revision,
            "content_bytes": len(self.content),
            "metadata": self.metadata,
            "updated_at": self.updated_at.isoformat().replace("+00:00", "Z"),
            "searchable": self.searchable,
        }


@dataclass
class FakeIndex:
    organization: str
    name: str
    id: str
    created_at: datetime
    state: str = "ready"
    description: str = ""
    tags: dict[str, str] = field(default_factory=dict)
    documents: dict[str, StoredDocument] = field(default_factory=dict)
    idempotency: dict[str, tuple[str, Any]] = field(default_factory=dict)

    @property
    def ref(self) -> str:
        return f"{self.organization}/{self.name}"

    def to_json(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organization": self.organization,
            "name": self.name,
            "canonical_id": self.id,
            "description": self.description,
            "tags": dict(self.tags),
            "state": self.state,
            "document_count": len(self.documents),
            "content_bytes": sum(len(d.content) for d in self.documents.values()),
            "created_at": self.created_at.isoformat().replace("+00:00", "Z"),
        }


@dataclass
class Fault:
    times: int
    status: int | None = None
    code: str = "internal_error"
    message: str = "the request could not be completed"
    retry_after: int | None = None
    exception: Exception | None = None
    method: str | None = None
    path_suffix: str | None = None
    when: Callable[[httpx.Request], bool] | None = None

    def matches(self, request: httpx.Request) -> bool:
        if self.method is not None and request.method != self.method:
            return False
        if self.path_suffix is not None and not request.url.path.endswith(self.path_suffix):
            return False
        return self.when is None or self.when(request)


class FakeGrepvine:
    """The fake service. Mount ``httpx.MockTransport(fake.handle)`` on a client."""

    def __init__(self, api_key: str = API_KEY) -> None:
        self.api_key = api_key
        self.organizations: dict[str, dict[str, Any]] = {}
        self.indexes: dict[tuple[str, str], FakeIndex] = {}
        self.requests: list[httpx.Request] = []
        self.faults: list[Fault] = []
        self.quote_etag = False
        self.search_truncate_after: int | None = None
        self.now = datetime(2026, 9, 6, 12, 0, tzinfo=UTC)
        self._revisions = 0

    # -- seeding -------------------------------------------------------------

    def add_organization(self, name: str, role: str = "owner") -> dict[str, Any]:
        entry = {
            "id": str(uuid.uuid4()),
            "name": name,
            "role": role,
            "created_at": self.now.isoformat().replace("+00:00", "Z"),
        }
        self.organizations[name.lower()] = entry
        return entry

    def add_index(
        self,
        ref: str,
        *,
        state: str = "ready",
        description: str = "",
        tags: dict[str, str] | None = None,
    ) -> FakeIndex:
        organization, name = ref.split("/", 1)
        if organization.lower() not in self.organizations:
            self.add_organization(organization)
        organization = self.organizations[organization.lower()]["name"]
        index = FakeIndex(
            organization, name, str(uuid.uuid4()), self.now, state, description, dict(tags or {})
        )
        self.indexes[(organization.lower(), name.lower())] = index
        return index

    def add_document(
        self,
        ref: str,
        key: str,
        content: bytes | str,
        metadata: dict[str, Any] | None = None,
    ) -> StoredDocument:
        index = self._index(*ref.split("/", 1))
        data = content.encode() if isinstance(content, str) else content
        document = StoredDocument(key, data, metadata or {}, self._revision(), self.now)
        index.documents[key] = document
        return document

    def fail_next(
        self,
        status: int,
        *,
        code: str = "internal_error",
        message: str = "the request could not be completed",
        retry_after: int | None = None,
        times: int = 1,
        method: str | None = None,
        path_suffix: str | None = None,
        when: Callable[[httpx.Request], bool] | None = None,
    ) -> None:
        self.faults.append(
            Fault(times, status, code, message, retry_after, None, method, path_suffix, when)
        )

    def raise_next(self, exception: Exception, *, times: int = 1) -> None:
        self.faults.append(Fault(times, exception=exception))

    def _revision(self) -> str:
        self._revisions += 1
        return f"rev-{self._revisions:04d}"

    # -- request handling ----------------------------------------------------

    def handle(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        request_id = f"req-{len(self.requests)}"
        for fault in list(self.faults):
            if fault.times > 0 and fault.matches(request):
                fault.times -= 1
                if fault.times == 0:
                    self.faults.remove(fault)
                if fault.exception is not None:
                    raise fault.exception
                assert fault.status is not None
                headers = {"X-Request-ID": request_id}
                if fault.retry_after is not None:
                    headers["Retry-After"] = str(fault.retry_after)
                return httpx.Response(
                    fault.status,
                    json={"code": fault.code, "reason": "fault", "error": fault.message},
                    headers=headers,
                )
        try:
            response = self._route(request)
        except RejectError as rejection:
            body: dict[str, Any] = {
                "code": rejection.code,
                "reason": rejection.reason,
                "error": rejection.message,
            }
            response = httpx.Response(rejection.status, json=body, headers=rejection.headers)
        response.headers["X-Request-ID"] = request_id
        return response

    def _route(self, request: httpx.Request) -> httpx.Response:
        if request.headers.get("Authorization") != f"Bearer {self.api_key}":
            raise RejectError(
                401, "unauthenticated", "authentication is required", reason="authentication"
            )
        path = request.url.raw_path.split(b"?", 1)[0].decode()
        if not path.startswith("/v1/"):
            raise RejectError(404, "not_found", "the resource does not exist", reason="resource")
        path = path[len("/v1") :]
        method = request.method

        if path == "/organizations" and method == "GET":
            return self._list_organizations(request)
        m = re.fullmatch(r"/organizations/([^/]+)", path)
        if m and method == "GET":
            return httpx.Response(200, json=self._organization(unquote(m.group(1))))
        m = re.fullmatch(r"/organizations/([^/]+)/indexes", path)
        if m and method == "GET":
            return self._list_indexes(request, unquote(m.group(1)))
        if m and method == "POST":
            return self._create_index(request, unquote(m.group(1)))
        m = re.fullmatch(r"/organizations/([^/]+)/indexes/([^/:]+)", path)
        if m and method == "GET":
            return httpx.Response(
                200, json=self._index(unquote(m.group(1)), unquote(m.group(2))).to_json()
            )
        if m and method == "PATCH":
            return self._update_index(
                request, self._index(unquote(m.group(1)), unquote(m.group(2)))
            )
        if m and method == "DELETE":
            index = self._index(unquote(m.group(1)), unquote(m.group(2)))
            del self.indexes[(index.organization.lower(), index.name.lower())]
            return httpx.Response(202)
        m = re.fullmatch(r"/organizations/([^/]+)/indexes/([^/:]+)/query", path)
        if m and method == "POST":
            return self._query(request, self._index(unquote(m.group(1)), unquote(m.group(2))))
        m = re.fullmatch(r"/organizations/([^/]+)/indexes/([^/:]+)/objects", path)
        if m and method == "GET":
            return self._list_documents(
                request, self._index(unquote(m.group(1)), unquote(m.group(2)))
            )
        if m and method == "PUT":
            return self._put_document(
                request, self._index(unquote(m.group(1)), unquote(m.group(2)))
            )
        m = re.fullmatch(r"/organizations/([^/]+)/indexes/([^/:]+)/objects:batch", path)
        if m and method == "POST":
            return self._put_batch(request, self._index(unquote(m.group(1)), unquote(m.group(2))))
        m = re.fullmatch(r"/organizations/([^/]+)/indexes/([^/:]+)/objects:delete", path)
        if m and method == "POST":
            return self._delete_batch(
                request, self._index(unquote(m.group(1)), unquote(m.group(2)))
            )
        m = re.fullmatch(r"/organizations/([^/]+)/indexes/([^/:]+)/objects/([^/]+)", path)
        if m and method == "GET":
            index = self._index(unquote(m.group(1)), unquote(m.group(2)))
            return self._get_document(request, index, unquote(m.group(3)))
        if m and method == "DELETE":
            index = self._index(unquote(m.group(1)), unquote(m.group(2)))
            return self._delete_document(request, index, unquote(m.group(3)))
        raise RejectError(404, "not_found", "the resource does not exist", reason="resource")

    # -- lookups -------------------------------------------------------------

    def _organization(self, name: str) -> dict[str, Any]:
        try:
            return self.organizations[name.lower()]
        except KeyError:
            raise RejectError(
                404, "not_found", "the resource does not exist or is not visible", reason="resource"
            ) from None

    def _index(self, organization: str, name: str) -> FakeIndex:
        try:
            return self.indexes[(organization.lower(), name.lower())]
        except KeyError:
            raise RejectError(
                404, "not_found", "the resource does not exist or is not visible", reason="resource"
            ) from None

    # -- pagination ----------------------------------------------------------

    def _request_hash(self, request: httpx.Request) -> str:
        params = sorted((k, v) for k, v in request.url.params.multi_items() if k != "page")
        digest = hashlib.sha256()
        digest.update(request.url.path.encode())
        digest.update(json.dumps(params).encode())
        digest.update(request.content)
        return digest.hexdigest()

    def _page_args(self, request: httpx.Request) -> tuple[int, int]:
        """The ``amount`` and the decoded cursor of a paged request."""
        raw_amount = request.url.params.get("amount", "50")
        if not raw_amount.isdigit() or not 1 <= int(raw_amount) <= MAX_AMOUNT:
            raise RejectError(400, "invalid_amount", "amount must be between 1 and 200")
        token = request.url.params.get("page")
        if not token:
            return int(raw_amount), 0
        try:
            payload = json.loads(base64.urlsafe_b64decode(token.encode()))
            cursor = int(payload["c"])
            expires = datetime.fromisoformat(payload["e"])
            if payload["h"] != self._request_hash(request) or expires <= self.now:
                raise ValueError
        except (ValueError, KeyError, TypeError):
            raise RejectError(
                400, "invalid_page", "the page token is invalid or expired", reason="pagination"
            ) from None
        return int(raw_amount), cursor

    def _token(self, request: httpx.Request, cursor: int) -> str:
        payload = {
            "c": cursor,
            "h": self._request_hash(request),
            "e": (self.now + TOKEN_TTL).isoformat(),
        }
        return base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()

    def _page(
        self, request: httpx.Request, items: list[Any], extra: dict[str, Any] | None = None
    ) -> httpx.Response:
        amount, cursor = self._page_args(request)
        chunk = items[cursor : cursor + amount]
        has_next = cursor + amount < len(items)
        body: dict[str, Any] = {
            "results": chunk,
            "pagination": {
                "next_page_id": self._token(request, cursor + amount) if has_next else "",
                "has_next": has_next,
            },
        }
        if extra:
            body.update(extra)
        return httpx.Response(200, json=body)

    # -- organizations and indexes ------------------------------------------

    def _list_organizations(self, request: httpx.Request) -> httpx.Response:
        items = [self.organizations[name] for name in sorted(self.organizations)]
        return self._page(request, items)

    def _list_indexes(self, request: httpx.Request, organization: str) -> httpx.Response:
        self._organization(organization)
        prefix = request.url.params.get("prefix", "")
        items = [
            index.to_json()
            for (org, name), index in sorted(self.indexes.items())
            if org == organization.lower() and name.startswith(prefix.lower())
        ]
        return self._page(request, items)

    def _create_index(self, request: httpx.Request, organization: str) -> httpx.Response:
        self._organization(organization)
        body = self._json(request)
        name = body.get("name")
        if not isinstance(name, str) or not INDEX_NAME.match(name):
            raise RejectError(400, "invalid_name", "the index name is invalid")
        if (organization.lower(), name.lower()) in self.indexes:
            raise RejectError(
                409, "conflict", "the request conflicts with current state", reason="state"
            )
        description = self._description(body.get("description", ""))
        tags = self._tags(body.get("tags", {}), removals=False)
        index = self.add_index(f"{organization}/{name}", description=description, tags=tags)
        return httpx.Response(201, json=index.to_json())

    def _update_index(self, request: httpx.Request, index: FakeIndex) -> httpx.Response:
        """PATCH semantics: a field absent from the body is left as it is."""
        body = self._json(request)
        if "description" not in body and "tags" not in body:
            raise RejectError(400, "invalid_request", "the request is invalid")
        description = self._description(body["description"]) if "description" in body else None
        tags = self._merge_tags(index.tags, body["tags"]) if "tags" in body else None
        if description is not None:
            index.description = description
        if tags is not None:
            index.tags = tags
        return httpx.Response(200, json=index.to_json())

    @staticmethod
    def _description(value: Any) -> str:
        if not isinstance(value, str) or len(value) > 16384:
            raise RejectError(400, "invalid_request", "the request is invalid")
        return value

    @staticmethod
    def _tags(value: Any, *, removals: bool) -> dict[str, Any]:
        """Check a tag map the way the service does; ``removals`` allows null values."""
        invalid = RejectError(400, "invalid_request", "the request is invalid")
        if not isinstance(value, dict) or len(value) > MAX_TAGS:
            raise invalid
        for key, item in value.items():
            if not 1 <= len(key) <= MAX_TAG_KEY_LENGTH:
                raise invalid
            if any(char.isspace() or unicodedata.category(char) == "Cc" for char in key):
                raise invalid
            if item is None and removals:
                continue
            if not isinstance(item, str) or len(item) > MAX_TAG_VALUE_LENGTH:
                raise invalid
            if any(unicodedata.category(char) == "Cc" for char in item):
                raise invalid
        return value

    def _merge_tags(self, current: dict[str, str], changes: Any) -> dict[str, str]:
        merged = dict(current)
        for key, value in self._tags(changes, removals=True).items():
            if value is None:
                merged.pop(key, None)
            else:
                merged[key] = value
        if len(merged) > MAX_TAGS:
            raise RejectError(400, "invalid_request", "the request is invalid")
        return merged

    # -- documents -----------------------------------------------------------

    def _json(self, request: httpx.Request) -> dict[str, Any]:
        try:
            body = json.loads(request.content)
        except ValueError:
            raise RejectError(400, "invalid_request", "the request is invalid") from None
        if not isinstance(body, dict):
            raise RejectError(400, "invalid_request", "the request is invalid")
        return body

    def _idempotency_key(self, request: httpx.Request) -> str:
        key = request.headers.get("Idempotency-Key")
        if key is None or not 16 <= len(key) <= 128:
            raise RejectError(
                400, "invalid_request", "Idempotency-Key must be 16 to 128 characters"
            )
        return key

    def _replay(self, index: FakeIndex, key: str, digest: str) -> Any | None:
        stored = index.idempotency.get(key)
        if stored is None:
            return None
        if stored[0] != digest:
            raise RejectError(409, "conflict", "idempotency key payload changed", reason="state")
        return stored[1]

    @staticmethod
    def _precondition_holds(
        index: FakeIndex, key: str, if_match: str | None, if_none_match: str | None
    ) -> bool:
        existing = index.documents.get(key)
        if if_match is not None and (existing is None or existing.revision != if_match):
            return False
        return not (if_none_match is not None and existing is not None)

    def _check_precondition(
        self, index: FakeIndex, key: str, if_match: str | None, if_none_match: str | None
    ) -> None:
        if not self._precondition_holds(index, key, if_match, if_none_match):
            raise RejectError(
                412, "precondition_failed", "a mutation precondition failed", reason="precondition"
            )

    @staticmethod
    def _rejected(key: str, code: str) -> dict[str, Any]:
        """The result of a document a batch left unchanged, as the service renders it."""
        if code == "not_found":
            error = {"code": code, "reason": "resource", "error": "the document does not exist"}
        else:
            error = {
                "code": code,
                "reason": "precondition",
                "error": "the document's precondition failed",
            }
        return {"key": key, "error": error}

    def _store(
        self, index: FakeIndex, key: str, content: bytes, metadata: dict[str, Any]
    ) -> dict[str, Any]:
        document = StoredDocument(key, content, metadata, self._revision(), self.now)
        index.documents[key] = document
        return {"key": key, "revision": document.revision}

    def _put_document(self, request: httpx.Request, index: FakeIndex) -> httpx.Response:
        idem = self._idempotency_key(request)
        content_type = request.headers.get("Content-Type", "")
        if not content_type.startswith("multipart/form-data"):
            raise RejectError(
                400, "invalid_upload", "the upload could not be read", reason="upload"
            )
        message = email.message_from_bytes(
            b"Content-Type: " + content_type.encode() + b"\r\n\r\n" + request.content,
            policy=email.policy.HTTP,
        )
        fields: dict[str, Any] = {}
        for part in message.iter_parts():
            name = part.get_param("name", header="content-disposition")
            payload = part.get_payload(decode=True)
            if not isinstance(payload, bytes):
                raise RejectError(
                    400, "invalid_upload", "the upload could not be read", reason="upload"
                )
            if name == "content":
                if part.get_filename() is None:
                    raise RejectError(
                        400, "invalid_upload", "content must be a file part", reason="upload"
                    )
                fields["content"] = payload
            elif isinstance(name, str):
                fields[name] = payload.decode()
        key = fields.get("key")
        if not key or "content" not in fields:
            raise RejectError(
                400, "invalid_upload", "key and content are required", reason="upload"
            )
        try:
            metadata = json.loads(fields["metadata"]) if "metadata" in fields else {}
        except ValueError:
            raise RejectError(400, "invalid_metadata", "metadata is invalid") from None
        digest = hashlib.sha256(request.content).hexdigest()
        replay = self._replay(index, idem, digest)
        if replay is not None:
            return httpx.Response(200, json=replay)
        if_match = request.headers.get("If-Match")
        if_none_match = request.headers.get("If-None-Match")
        if if_match is not None and if_none_match is not None:
            raise RejectError(
                400, "invalid_precondition", "If-Match and If-None-Match cannot be combined"
            )
        self._check_precondition(index, key, if_match, if_none_match)
        result = self._store(index, key, fields["content"], metadata)
        index.idempotency[idem] = (digest, result)
        return httpx.Response(200, json=result)

    def _put_batch(self, request: httpx.Request, index: FakeIndex) -> httpx.Response:
        idem = self._idempotency_key(request)
        if not request.headers.get("Content-Type", "").startswith("application/x-ndjson"):
            raise RejectError(400, "invalid_ndjson", "the NDJSON batch is invalid")
        records: list[dict[str, Any]] = []
        for line in request.content.split(b"\n"):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except ValueError:
                raise RejectError(400, "invalid_ndjson", "the NDJSON batch is invalid") from None
            if not isinstance(record, dict) or "key" not in record or "content" not in record:
                raise RejectError(400, "invalid_ndjson", "the NDJSON batch is invalid")
            records.append(record)
        if not records:
            raise RejectError(400, "empty_batch", "the batch is empty")
        total = sum(len(str(r["content"]).encode()) for r in records)
        if len(records) > MAX_BATCH_RECORDS or total > MAX_BATCH_BYTES:
            raise RejectError(
                413, "batch_too_large", "the batch exceeds its limits", reason="limit"
            )
        keys = [r["key"] for r in records]
        if len(set(keys)) != len(keys):
            raise RejectError(400, "invalid_request", "the batch repeats a key")
        digest = hashlib.sha256(request.content).hexdigest()
        replay = self._replay(index, idem, digest)
        if replay is not None:
            return httpx.Response(200, json=replay)
        results = []
        for record in records:
            key = record["key"]
            if not self._precondition_holds(
                index, key, record.get("if_match"), record.get("if_none_match")
            ):
                results.append(self._rejected(key, "precondition_failed"))
                continue
            content = str(record["content"]).encode()
            results.append(self._store(index, key, content, record.get("metadata") or {}))
        body = {"results": results}
        index.idempotency[idem] = (digest, body)
        return httpx.Response(200, json=body)

    def _delete_document(
        self, request: httpx.Request, index: FakeIndex, key: str
    ) -> httpx.Response:
        idem = self._idempotency_key(request)
        digest = hashlib.sha256(f"delete:{key}".encode()).hexdigest()
        replay = self._replay(index, idem, digest)
        if replay is not None:
            return httpx.Response(200, json=replay)
        if key not in index.documents:
            raise RejectError(404, "not_found", "the resource does not exist", reason="resource")
        self._check_precondition(index, key, request.headers.get("If-Match"), None)
        del index.documents[key]
        result = {"key": key, "revision": self._revision()}
        index.idempotency[idem] = (digest, result)
        return httpx.Response(200, json=result)

    def _delete_batch(self, request: httpx.Request, index: FakeIndex) -> httpx.Response:
        idem = self._idempotency_key(request)
        body = self._json(request)
        objects = body.get("objects")
        if not isinstance(objects, list) or not objects:
            raise RejectError(400, "invalid_request", "objects must be a non-empty list")
        if len(objects) > MAX_BATCH_RECORDS:
            raise RejectError(
                413, "batch_too_large", "the batch exceeds its limits", reason="limit"
            )
        digest = hashlib.sha256(request.content).hexdigest()
        replay = self._replay(index, idem, digest)
        if replay is not None:
            return httpx.Response(200, json=replay)
        results = []
        for record in objects:
            key = record["key"]
            if not self._precondition_holds(index, key, record.get("if_match"), None):
                results.append(self._rejected(key, "precondition_failed"))
            elif key not in index.documents:
                results.append(self._rejected(key, "not_found"))
            else:
                del index.documents[key]
                results.append({"key": key, "revision": self._revision()})
        response_body = {"results": results}
        index.idempotency[idem] = (digest, response_body)
        return httpx.Response(200, json=response_body)

    def _get_document(self, request: httpx.Request, index: FakeIndex, key: str) -> httpx.Response:
        document = index.documents.get(key)
        if document is None:
            raise RejectError(404, "not_found", "the resource does not exist", reason="resource")
        etag = f'"{document.revision}"' if self.quote_etag else document.revision
        headers = {
            "ETag": etag,
            "X-Grepvine-Metadata": json.dumps(document.metadata),
            "Accept-Ranges": "bytes",
            "Content-Type": "application/octet-stream",
        }
        range_header = request.headers.get("Range")
        if range_header is None:
            return httpx.Response(200, content=document.content, headers=headers)
        m = re.fullmatch(r"bytes=(\d*)-(\d*)", range_header)
        if m is None or "," in range_header or (not m.group(1) and not m.group(2)):
            raise RejectError(400, "invalid_range", "the Range header must contain one bytes range")
        size = len(document.content)
        if not m.group(1):
            start, end = max(size - int(m.group(2)), 0), size - 1
        else:
            start = int(m.group(1))
            end = min(int(m.group(2)), size - 1) if m.group(2) else size - 1
        if start >= size or start > end:
            raise RejectError(
                416,
                "range_not_satisfiable",
                "the byte range does not overlap the document",
                reason="range",
                headers={"Content-Range": f"bytes */{size}"},
            )
        headers["Content-Range"] = f"bytes {start}-{end}/{size}"
        return httpx.Response(206, content=document.content[start : end + 1], headers=headers)

    def _list_documents(self, request: httpx.Request, index: FakeIndex) -> httpx.Response:
        prefix = request.url.params.get("prefix", "")
        delimiter = request.url.params.get("delimiter")
        if delimiter is not None and not 1 <= len(delimiter) <= 16:
            raise RejectError(400, "invalid_delimiter", "delimiter must be 1 to 16 characters")
        results: list[dict[str, Any]] = []
        prefixes: list[str] = []
        for key in sorted(index.documents, key=lambda k: k.encode()):
            if not key.startswith(prefix):
                continue
            if delimiter:
                rest = key[len(prefix) :]
                position = rest.find(delimiter)
                if position >= 0:
                    folded = prefix + rest[: position + len(delimiter)]
                    if folded not in prefixes:
                        prefixes.append(folded)
                    continue
            results.append(index.documents[key].summary())
        return self._page(request, results, {"common_prefixes": prefixes})

    # -- search --------------------------------------------------------------

    def _query(self, request: httpx.Request, index: FakeIndex) -> httpx.Response:
        body = self._json(request)
        allowed = {
            "pattern",
            "mode",
            "case_sensitive",
            "whole_word",
            "multiline",
            "filter",
            "lines_before",
            "lines_after",
        }
        if set(body) - allowed or "pattern" not in body:
            raise RejectError(400, "invalid_request", "the request is invalid")
        mode = body.get("mode", "regex")
        whole_word = body.get("whole_word", False)
        if whole_word and mode != "literal":
            raise RejectError(
                400, "invalid_pattern", "whole-word matching is valid only in literal mode"
            )
        pattern = body["pattern"] if mode == "regex" else re.escape(body["pattern"])
        if whole_word:
            pattern = rf"(?<!\w){pattern}(?!\w)"
        flags = re.MULTILINE
        if not body.get("case_sensitive", True):
            flags |= re.IGNORECASE
        try:
            compiled = re.compile(pattern.encode("utf-8"), flags)
        except re.error as exc:
            raise RejectError(400, "invalid_pattern", str(exc)) from None
        predicate = self._compile_filter(body.get("filter"))
        multiline = body.get("multiline", False)
        before, after = int(body.get("lines_before", 0)), int(body.get("lines_after", 0))
        amount, cursor = self._page_args(request)

        units: list[tuple[StoredDocument, int]] = []  # (document, line index or match index)
        prepared: dict[str, list[bytes]] = {}
        for key in sorted(index.documents, key=lambda k: k.encode()):
            document = index.documents[key]
            if not document.searchable or not predicate(document.metadata):
                continue
            lines = document.content.split(b"\n")
            prepared[key] = lines
            if multiline:
                units.extend(
                    (document, i) for i in range(len(list(compiled.finditer(document.content))))
                )
            else:
                units.extend((document, i) for i in range(len(lines)))

        results: list[dict[str, Any]] = []
        examined = 0
        position = cursor
        while position < len(units) and len(results) < amount:
            if self.search_truncate_after is not None and examined >= self.search_truncate_after:
                break
            document, ordinal = units[position]
            position += 1
            examined += 1
            lines = prepared[document.key]
            offsets = [0]
            for line in lines[:-1]:
                offsets.append(offsets[-1] + len(line) + 1)
            if multiline:
                match = list(compiled.finditer(document.content))[ordinal]
                first = max(i for i, off in enumerate(offsets) if off <= match.start())
                last = max(
                    i for i, off in enumerate(offsets) if off < max(match.end(), match.start() + 1)
                )
                text = b"\n".join(lines[first : last + 1])
                results.append(
                    self._result(
                        document, lines, offsets, first, last, text, [match.span()], before, after
                    )
                )
            else:
                line = lines[ordinal]
                spans = [
                    (offsets[ordinal] + m.start(), offsets[ordinal] + m.end())
                    for m in compiled.finditer(line)
                ]
                if spans:
                    results.append(
                        self._result(
                            document, lines, offsets, ordinal, ordinal, line, spans, before, after
                        )
                    )
        has_next = position < len(units)
        return httpx.Response(
            200,
            json={
                "results": results,
                "pagination": {
                    "next_page_id": self._token(request, position) if has_next else "",
                    "has_next": has_next,
                },
            },
        )

    def _result(
        self,
        document: StoredDocument,
        lines: list[bytes],
        offsets: list[int],
        first: int,
        last: int,
        text: bytes,
        spans: list[tuple[int, int]],
        before: int,
        after: int,
    ) -> dict[str, Any]:
        result: dict[str, Any] = {
            "key": document.key,
            "revision": document.revision,
            "line_number": first + 1,
            "last_line_number": last + 1,
            "line_start_offset": offsets[first],
            "line_end_offset": offsets[last] + len(lines[last]),
            "text_start_offset": offsets[first],
            "text_line_number": first + 1,
            "text": text.decode("utf-8"),
            "matches": [{"offset": start, "length": end - start} for start, end in spans],
            "text_truncated": False,
            "matches_truncated": False,
        }
        if before:
            result["lines_before"] = [
                {"line_number": i + 1, "text": lines[i].decode("utf-8"), "text_truncated": False}
                for i in range(max(0, first - before), first)
            ]
        if after:
            result["lines_after"] = [
                {"line_number": i + 1, "text": lines[i].decode("utf-8"), "text_truncated": False}
                for i in range(last + 1, min(len(lines), last + 1 + after))
            ]
        return result

    _FILTER = re.compile(
        r"^\s*(?P<field>[A-Za-z_][A-Za-z0-9_]*)\s+(?P<op>=|!=|<=|>=|<|>|STARTSWITH)\s+"
        r"(?P<value>'(?:[^']|'')*'|-?\d+(?:\.\d+)?)\s*$",
        re.IGNORECASE,
    )

    def _compile_filter(self, expression: str | None) -> Callable[[dict[str, Any]], bool]:
        if not expression:
            return lambda metadata: True
        clauses: list[tuple[str, str, Any]] = []
        for raw in re.split(r"\s+AND\s+", expression, flags=re.IGNORECASE):
            clause = raw.strip()
            if clause.startswith("(") and clause.endswith(")"):
                clause = clause[1:-1]
            m = self._FILTER.match(clause)
            if m is None:
                raise RejectError(400, "invalid_filter", f"cannot parse filter near {clause!r}")
            value: Any = m.group("value")
            if value.startswith("'"):
                value = value[1:-1].replace("''", "'")
            elif "." in value:
                value = float(value)
            else:
                value = int(value)
            clauses.append((m.group("field"), m.group("op").upper(), value))

        def predicate(metadata: dict[str, Any]) -> bool:
            for name, op, expected in clauses:
                tagged = metadata.get(name)
                actual = tagged.get("value") if isinstance(tagged, dict) else tagged
                if actual is None:
                    return False
                if op == "STARTSWITH":
                    if not isinstance(actual, str) or not isinstance(expected, str):
                        return False
                    ok = actual.startswith(expected)
                else:
                    try:
                        ok = {
                            "=": actual == expected,
                            "!=": actual != expected,
                            "<": actual < expected,
                            "<=": actual <= expected,
                            ">": actual > expected,
                            ">=": actual >= expected,
                        }[op]
                    except TypeError:
                        return False
                if not ok:
                    return False
            return True

        return predicate
