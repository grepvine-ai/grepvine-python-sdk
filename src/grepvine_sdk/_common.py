"""Wire encoding and response handling shared by sync and async clients."""

import json
import math
import uuid
from collections.abc import Iterable, Mapping
from datetime import datetime
from io import BytesIO
from typing import Any, BinaryIO, NotRequired, TypedDict, TypeVar

from .errors import ApiError, BatchError
from .generated.models import (
    Error,
    MutationResult,
    PutDocumentForm,
    PutDocumentIfNoneMatch,
    QueryRequest,
    QueryRequestMode,
)
from .generated.types import UNSET, File, Response

MetadataScalar = str | int | float | bool | datetime
MetadataInput = Mapping[str, MetadataScalar]


class Document(TypedDict):
    """A text document for one batch request."""

    key: str
    content: str
    metadata: NotRequired[MetadataInput]
    if_match: NotRequired[str]
    if_none_match: NotRequired[bool]


T = TypeVar("T")


def checked(response: Response[Any]) -> None:
    if not 200 <= response.status_code < 300 or isinstance(response.parsed, Error):
        raise ApiError(
            response.status_code,
            response.parsed if isinstance(response.parsed, Error) else None,
            response.headers,
        )


def unwrap(response: Response[T | Error], model: type[T]) -> T:
    checked(response)
    if not isinstance(response.parsed, model):
        raise ApiError(response.status_code, None, response.headers)
    return response.parsed


def mutation(response: Response[MutationResult | Error]) -> MutationResult:
    item = unwrap(response, MutationResult)
    if isinstance(item.error, Error):
        raise ApiError(response.status_code, item.error, response.headers)
    if not item.revision:
        raise ApiError(response.status_code, None, response.headers)
    return item


def mutations(
    results: list[MutationResult], request_id: str | None, raise_on_error: bool
) -> list[MutationResult]:
    if raise_on_error and any(
        isinstance(item.error, Error) or not item.revision for item in results
    ):
        raise BatchError(results, request_id)
    return results


def reference(ref: str) -> tuple[str, str]:
    parts = ref.split("/")
    if len(parts) != 2 or not all(parts):
        raise ValueError("Use an index reference in the form organization/index")
    return parts[0], parts[1]


def endpoint_url(endpoint: str) -> str:
    endpoint = endpoint.rstrip("/")
    return endpoint if endpoint.endswith("/v1") else endpoint + "/v1"


def make_idempotency_key(key: str | None) -> str:
    if key is not None:
        if not key:
            raise ValueError("An idempotency key cannot be empty")
        return key
    return str(uuid.uuid4())


def metadata_values(metadata: MetadataInput) -> dict[str, dict[str, Any]]:
    encoded: dict[str, dict[str, Any]] = {}
    for key, value in metadata.items():
        if isinstance(value, bool):
            kind = "boolean"
        elif isinstance(value, int):
            if not -(2**63) <= value < 2**63:
                raise ValueError("Integer metadata must fit in a signed 64-bit value")
            kind = "integer"
        elif isinstance(value, float):
            if not math.isfinite(value):
                raise ValueError("Number metadata must be finite")
            kind = "number"
        elif isinstance(value, datetime):
            if value.utcoffset() is None:
                raise ValueError("Timestamp metadata needs a timezone")
            kind = "timestamp"
            value = value.isoformat()
        elif isinstance(value, str):
            kind = "string"
        else:
            raise TypeError("Metadata values must be strings, numbers, booleans, or timestamps")
        encoded[key] = {"type": kind, "value": value}
    return encoded


def form(
    key: str, content: str | bytes | BinaryIO, metadata: MetadataInput | None
) -> PutDocumentForm:
    payload = (
        BytesIO(content.encode() if isinstance(content, str) else content)
        if isinstance(content, str | bytes)
        else content
    )
    return PutDocumentForm(
        key=key,
        content=File(payload=payload, file_name=key.rsplit("/", 1)[-1]),
        metadata=json.dumps(metadata_values(metadata), allow_nan=False)
        if metadata is not None
        else UNSET,
    )


def batch_body(documents: Iterable[Document]) -> File:
    lines = []
    total = 0
    for number, document in enumerate(documents, 1):
        if number > 2048:
            raise ValueError("put_many accepts at most 2048 documents per call")
        content = document["content"]
        if not isinstance(content, str):
            raise TypeError("Batch document content must be text; use put for binary content")
        total += len(content.encode("utf-8"))
        if total > 16 * 1024 * 1024:
            raise ValueError("put_many accepts at most 16 MiB of text per call")
        record: dict[str, Any] = {"key": document["key"], "content": content}
        if "metadata" in document:
            record["metadata"] = metadata_values(document["metadata"])
        if "if_match" in document:
            record["if_match"] = document["if_match"]
        if document.get("if_none_match"):
            record["if_none_match"] = "*"
        lines.append(json.dumps(record, ensure_ascii=False, allow_nan=False, sort_keys=True) + "\n")
    if not lines:
        raise ValueError("put_many needs at least one document")
    return File(payload=BytesIO("".join(lines).encode("utf-8")))


def write_options(key: str | None, if_match: str | None, if_none_match: bool) -> dict[str, Any]:
    return {
        "idempotency_key": make_idempotency_key(key),
        "if_match": if_match if if_match is not None else UNSET,
        "if_none_match": PutDocumentIfNoneMatch.VALUE_0 if if_none_match else UNSET,
    }


def query(
    pattern: str,
    *,
    filter: str | None = None,
    literal: bool = False,
    case_sensitive: bool = True,
    whole_word: bool = False,
    multiline: bool = False,
    lines_before: int = 0,
    lines_after: int = 0,
) -> QueryRequest:
    return QueryRequest(
        pattern=pattern,
        mode=QueryRequestMode.LITERAL if literal else QueryRequestMode.REGEX,
        filter_=filter if filter is not None else UNSET,
        case_sensitive=case_sensitive,
        whole_word=whole_word,
        multiline=multiline,
        lines_before=lines_before,
        lines_after=lines_after,
    )


def poll_options(timeout: float, interval: float) -> None:
    if not math.isfinite(timeout) or timeout <= 0 or not math.isfinite(interval) or interval <= 0:
        raise ValueError("Readiness timeout and interval must be positive finite numbers")
