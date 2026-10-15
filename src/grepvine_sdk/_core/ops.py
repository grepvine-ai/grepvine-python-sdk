"""Every API operation, written once as an effect generator.

Each function that names a module of ``_generated.api`` is the one place the
client calls that operation; ``tests/test_coverage.py`` checks that every
operation of the API has exactly one such function and that exactly one
client method uses it.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping, Sequence
from io import BytesIO
from typing import TYPE_CHECKING, Any
from uuid import UUID

from grepvine_sdk._core import build, parse
from grepvine_sdk._core.batching import (
    MAX_BATCH_RECORDS,
    BatchChunk,
    PutRecord,
    load_content,
    plan_batches,
)
from grepvine_sdk._core.effects import Call, Notify, Now, Op, Session, SetSession, Sleep
from grepvine_sdk._core.metadata import MetadataInput, document_metadata
from grepvine_sdk._core.paging import PageSource, resolve_page_size, validate_page_token
from grepvine_sdk._core.paths import check_key
from grepvine_sdk._core.responses import parsed
from grepvine_sdk._generated import models as api
from grepvine_sdk._generated.api.api_keys import create_api_key, list_api_keys, revoke_api_key
from grepvine_sdk._generated.api.authentication import (
    change_password,
    get_current_user,
    get_username_availability,
    login,
    logout,
    register_user,
)
from grepvine_sdk._generated.api.device_login import (
    approve_device_authorization,
    deny_device_authorization,
    poll_device_token,
    start_device_authorization,
)
from grepvine_sdk._generated.api.indexes import (
    create_index,
    delete_index,
    get_index,
    list_indexes,
    update_index,
)
from grepvine_sdk._generated.api.objects import (
    delete_document,
    delete_objects,
    get_document,
    list_documents,
    put_document,
    put_objects,
)
from grepvine_sdk._generated.api.organizations import (
    add_organization_member,
    create_organization,
    delete_organization,
    get_organization,
    list_organization_members,
    list_organizations,
    remove_organization_member,
    transfer_organization_ownership,
    update_organization_member,
)
from grepvine_sdk._generated.api.search import query_index
from grepvine_sdk._generated.types import UNSET, File
from grepvine_sdk.errors import (
    ConflictError,
    GrepvineError,
    InvalidRequestError,
    NotFoundError,
    PartialBatchError,
    PreconditionFailedError,
)
from grepvine_sdk.models import (
    APIKey,
    APIKeyCreated,
    DeviceAuthorization,
    Document,
    DocumentError,
    DocumentSummary,
    IndexData,
    Member,
    MutationResult,
    Organization,
    SearchResult,
    User,
    from_api,
)

if TYPE_CHECKING:
    from grepvine_sdk._core.batching import Content

SESSION_COOKIES = ("__Host-grepvine-session", "grepvine-session")
"""The session cookie, and its name on a development service without HTTPS."""
DEFAULT_WAIT_INTERVAL = 1.0
MIN_DEVICE_POLL_INTERVAL = 5.0
DEVICE_SLOW_DOWN_STEP = 5.0
_ROLES = ("admin", "developer", "reader")


# -- organizations ------------------------------------------------------------


def organizations_listing(
    *, limit: int | None, page: str | None, page_size: int | None
) -> PageSource[Organization]:
    return PageSource(
        operation=list_organizations,
        page_model=api.OrganizationPage,
        page_size=resolve_page_size(page_size, limit),
        limit=limit,
        start_page=validate_page_token(page),
        parse_item=lambda item: from_api(Organization._from_json, item),
    )


def get_organization_op(name: str) -> Op[Organization]:
    response = yield Call(get_organization, (name,))
    return from_api(Organization._from_json, parsed(response, api.Organization))


def create_organization_op(name: str) -> Op[Organization]:
    body = api.CreateOrganizationRequest(name=name)
    response = yield Call(create_organization, kwargs={"body": body})
    return from_api(Organization._from_json, parsed(response, api.Organization))


def delete_organization_op(name: str) -> Op[None]:
    yield Call(delete_organization, (name,))
    return None


def transfer_ownership_op(organization: str, user: str) -> Op[None]:
    body = api.TransferOwnershipRequest(user=user)
    yield Call(transfer_organization_ownership, (organization,), {"body": body})
    return None


# -- members ------------------------------------------------------------------


def _role(role: str) -> str:
    if role not in _ROLES:
        raise ValueError(f"role must be one of {', '.join(_ROLES)}; ownership is transferred")
    return role


def members_listing(
    organization: str, *, limit: int | None, page: str | None, page_size: int | None
) -> PageSource[Member]:
    return PageSource(
        operation=list_organization_members,
        page_model=api.MemberPage,
        args=(organization,),
        page_size=resolve_page_size(page_size, limit),
        limit=limit,
        start_page=validate_page_token(page),
        parse_item=lambda item: from_api(Member._from_json, item),
    )


def add_member_op(organization: str, user: str, role: str) -> Op[Member]:
    body = api.AddMemberRequest(user=user, role=api.AddMemberRequestRole(_role(role)))
    response = yield Call(add_organization_member, (organization,), {"body": body})
    return from_api(Member._from_json, parsed(response, api.Member))


def update_member_op(organization: str, user: str, role: str) -> Op[Member]:
    body = api.UpdateMemberRequest(role=api.UpdateMemberRequestRole(_role(role)))
    response = yield Call(update_organization_member, (organization, user), {"body": body})
    return from_api(Member._from_json, parsed(response, api.Member))


def remove_member_op(organization: str, user: str) -> Op[None]:
    yield Call(remove_organization_member, (organization, user))
    return None


# -- API keys -----------------------------------------------------------------


def api_keys_listing(
    *, limit: int | None, page: str | None, page_size: int | None
) -> PageSource[APIKey]:
    return PageSource(
        operation=list_api_keys,
        page_model=api.APIKeyPage,
        page_size=resolve_page_size(page_size, limit),
        limit=limit,
        start_page=validate_page_token(page),
        parse_item=lambda item: from_api(APIKey._from_json, item),
    )


def create_api_key_op(name: str) -> Op[APIKeyCreated]:
    if not 1 <= len(name) <= 128:
        raise ValueError("an API key name must be 1 to 128 characters")
    response = yield Call(create_api_key, kwargs={"body": api.CreateAPIKeyRequest(name=name)})
    return from_api(APIKeyCreated._from_json, parsed(response, api.APIKeyCreated))


def revoke_api_key_op(key_id: str | UUID) -> Op[None]:
    try:
        identifier = key_id if isinstance(key_id, UUID) else UUID(str(key_id))
    except ValueError:
        raise ValueError(f"{key_id!r} is not an API key id") from None
    yield Call(revoke_api_key, (identifier,))
    return None


# -- account ------------------------------------------------------------------


def _session(response: Any) -> Session | None:
    """The session a sign-in response starts: its cookie and CSRF token, when both are present."""
    token = response.headers.get("x-csrf-token")
    for header in response.headers.get_list("set-cookie"):
        name, _, rest = header.partition("=")
        cookie = rest.split(";", 1)[0].strip()
        if name.strip() in SESSION_COOKIES and cookie and token:
            return Session(cookie_name=name.strip(), cookie=cookie, csrf_token=token)
    return None


def register_op(name: str, email: str, password: str) -> Op[User]:
    body = api.RegisterRequest(name=name, email=email, password=password)
    response = yield Call(register_user, kwargs={"body": body}, auth=False)
    user = from_api(User._from_json, parsed(response, api.User))
    yield SetSession(_session(response))
    return user


def username_available_op(name: str) -> Op[bool]:
    response = yield Call(get_username_availability, (name,), auth=False)
    return bool(parsed(response, api.UsernameAvailability).available)


def login_op(identifier: str, password: str) -> Op[User]:
    body = api.LoginRequest(identifier=identifier, password=password)
    response = yield Call(login, kwargs={"body": body}, auth=False)
    user = from_api(User._from_json, parsed(response, api.User))
    session = _session(response)
    if session is None:
        raise GrepvineError("the service did not start a session")
    yield SetSession(session)
    return user


def logout_op() -> Op[None]:
    yield Call(logout)
    yield SetSession(None)
    return None


def me_op() -> Op[User]:
    response = yield Call(get_current_user)
    return from_api(User._from_json, parsed(response, api.User))


def change_password_op(current_password: str, new_password: str) -> Op[None]:
    body = api.ChangePasswordRequest(current_password=current_password, new_password=new_password)
    yield Call(change_password, kwargs={"body": body})
    return None


# -- device login -------------------------------------------------------------


def start_device_login_op(api_key_name: str) -> Op[DeviceAuthorization]:
    if not 1 <= len(api_key_name) <= 128:
        raise ValueError("an API key name must be 1 to 128 characters")
    body = api.DeviceAuthorizationRequest(api_key_name=api_key_name)
    response = yield Call(start_device_authorization, kwargs={"body": body}, auth=False)
    return from_api(DeviceAuthorization._from_json, parsed(response, api.DeviceAuthorization))


def poll_device_login_op(device_code: str) -> Op[APIKeyCreated | None]:
    body = api.DeviceTokenRequest(device_code=device_code)
    try:
        response = yield Call(poll_device_token, kwargs={"body": body}, auth=False)
    except InvalidRequestError as exc:
        if exc.code == "authorization_pending":
            return None
        raise
    return from_api(APIKeyCreated._from_json, parsed(response, api.APIKeyCreated))


def approve_device_login_op(user_code: str) -> Op[None]:
    body = api.DeviceDecisionRequest(user_code=user_code)
    yield Call(approve_device_authorization, kwargs={"body": body})
    return None


def deny_device_login_op(user_code: str) -> Op[None]:
    body = api.DeviceDecisionRequest(user_code=user_code)
    yield Call(deny_device_authorization, kwargs={"body": body})
    return None


def authorize_device_op(
    api_key_name: str, *, on_code: Callable[[DeviceAuthorization], Any], timeout: float | None
) -> Op[APIKeyCreated]:
    """Start a device login, report its code, and poll until the key is issued.

    Polling follows the service's interval and slows down when asked to. A
    denied or expired login raises the service's
    :class:`~grepvine_sdk.InvalidRequestError` (code ``"access_denied"`` or
    ``"expired_token"``); running past ``timeout`` or the login's own expiry
    raises :class:`TimeoutError`.
    """
    if timeout is not None and timeout <= 0:
        raise ValueError("timeout must be positive")
    authorization = yield from start_device_login_op(api_key_name)
    started = yield Now()
    yield Notify(on_code, authorization)
    deadline = started + authorization.expires_in
    if timeout is not None:
        deadline = min(deadline, started + timeout)
    interval = max(float(authorization.interval), MIN_DEVICE_POLL_INTERVAL)
    while True:
        now = yield Now()
        if now + interval > deadline:
            raise TimeoutError("the device login was not approved in time")
        yield Sleep(interval)
        try:
            key = yield from poll_device_login_op(authorization.device_code)
        except InvalidRequestError as exc:
            if exc.code != "slow_down":
                raise
            interval += DEVICE_SLOW_DOWN_STEP
            continue
        if key is not None:
            return key


# -- indexes ------------------------------------------------------------------


def _index_data(response: Any) -> IndexData:
    return from_api(IndexData._from_json, parsed(response, api.Index))


def indexes_listing(
    organization: str,
    *,
    prefix: str | None,
    limit: int | None,
    page: str | None,
    page_size: int | None,
) -> PageSource[IndexData]:
    return PageSource(
        operation=list_indexes,
        page_model=api.IndexPage,
        args=(organization,),
        kwargs={} if prefix is None else {"prefix": prefix},
        page_size=resolve_page_size(page_size, limit),
        limit=limit,
        start_page=validate_page_token(page),
        parse_item=lambda item: from_api(IndexData._from_json, item),
    )


def get_index_op(organization: str, index: str) -> Op[IndexData]:
    response = yield Call(get_index, (organization, index))
    return _index_data(response)


def index_exists_op(organization: str, index: str) -> Op[bool]:
    try:
        yield from get_index_op(organization, index)
    except NotFoundError:
        return False
    return True


def wait_until_ready_op(
    organization: str, index: str, *, timeout: float | None, interval: float
) -> Op[IndexData]:
    """Read the index until its state is ``ready``.

    An index that is being deleted never becomes ready, so it raises
    :class:`~grepvine_sdk.GrepvineError` at once; running past ``timeout``
    raises :class:`TimeoutError`.
    """
    if timeout is not None and timeout <= 0:
        raise ValueError("timeout must be positive")
    if interval <= 0:
        raise ValueError("interval must be positive")
    started = yield Now()
    while True:
        data = yield from get_index_op(organization, index)
        if data.state == "ready":
            return data
        if data.state != "creating":
            raise GrepvineError(f"index {data.ref} is {data.state} and will not become ready")
        now = yield Now()
        if timeout is not None and now + interval > started + timeout:
            raise TimeoutError(f"index {data.ref} was not ready within {timeout:g} seconds")
        yield Sleep(interval)


def create_index_op(
    organization: str,
    name: str,
    *,
    description: str | None,
    tags: Mapping[str, str] | None,
    exist_ok: bool = False,
) -> Op[IndexData]:
    body = api.CreateIndexRequest(name=name)
    if description is not None:
        body.description = build.index_description(description)
    if tags is not None:
        body.tags = api.IndexTags.from_dict(build.index_tags(tags))
    try:
        response = yield Call(create_index, (organization,), {"body": body})
    except ConflictError:
        if not exist_ok:
            raise
        try:
            return (yield from get_index_op(organization, name))
        except NotFoundError:
            # The index vanished between the two requests; report the original conflict.
            pass
        raise
    return _index_data(response)


def update_index_op(
    organization: str,
    index: str,
    *,
    description: str | None,
    tags: Mapping[str, str | None] | None,
) -> Op[IndexData]:
    """A PATCH carrying only the fields given; the service leaves the others as they are."""
    if description is None and tags is None:
        raise ValueError("nothing to change")
    body = api.UpdateIndexRequest()
    if description is not None:
        body.description = build.index_description(description)
    if tags is not None:
        body.tags = api.IndexTagChanges.from_dict(build.tag_changes(tags))
    response = yield Call(update_index, (organization, index), {"body": body})
    return _index_data(response)


def delete_index_op(organization: str, index: str) -> Op[None]:
    yield Call(delete_index, (organization, index))
    return None


# -- search -------------------------------------------------------------------


def search_listing(
    organization: str,
    index: str,
    pattern: str,
    *,
    regex: bool,
    case_sensitive: bool,
    whole_word: bool,
    multiline: bool,
    filter: str | None,
    filters: Sequence[str] | None,
    lines_before: int,
    lines_after: int,
    limit: int | None,
    page: str | None,
    page_size: int | None,
) -> PageSource[SearchResult]:
    body = build.query_request(
        pattern,
        regex=regex,
        case_sensitive=case_sensitive,
        whole_word=whole_word,
        multiline=multiline,
        filter=build.combine_filters(filter, filters),
        lines_before=lines_before,
        lines_after=lines_after,
    )
    return PageSource(
        operation=query_index,
        page_model=api.QueryPage,
        args=(organization, index),
        kwargs={"body": body},
        page_size=resolve_page_size(page_size, limit),
        limit=limit,
        start_page=validate_page_token(page),
        parse_item=lambda item: from_api(SearchResult._from_json, item),
    )


# -- documents ----------------------------------------------------------------


def _mutation_result(response: Any) -> MutationResult:
    return from_api(MutationResult._from_json, parsed(response, api.MutationResult))


def _mutation_results(response: Any, expected: int) -> list[MutationResult]:
    """The result of every document of a batch, in request order."""
    results = parsed(response, api.MutationBatchResult).results
    if len(results) != expected:
        raise GrepvineError(
            f"the service returned {len(results)} results for a batch of {expected} documents"
        )
    return [from_api(MutationResult._from_json, item) for item in results]


def put_document_op(
    organization: str,
    index: str,
    key: str,
    content: Content,
    *,
    new_id: Callable[[], str],
    metadata: MetadataInput | None = None,
    if_match: str | None = None,
    if_none_match: bool = False,
    idempotency_key: str | None = None,
) -> Op[MutationResult]:
    check_key(key)
    build.check_preconditions(if_match, if_none_match)
    idempotency = build.idempotency_key(idempotency_key or new_id())
    loaded = load_content(content)
    try:
        metadata_json = json.dumps(
            document_metadata(key, loaded.size, metadata, loaded.mtime), ensure_ascii=False
        )
        payload: Any = BytesIO(loaded.data) if isinstance(loaded.data, bytes) else loaded.data
        body = api.PutDocumentForm(
            key=key,
            content=File(
                payload=payload, file_name="content", mime_type="application/octet-stream"
            ),
            metadata=metadata_json,
        )
        response = yield Call(
            put_document,
            (organization, index),
            {
                "body": body,
                "idempotency_key": idempotency,
                "if_match": UNSET if if_match is None else if_match,
                "if_none_match": api.PutDocumentIfNoneMatch.VALUE_0 if if_none_match else UNSET,
            },
        )
        return _mutation_result(response)
    finally:
        if loaded.owned is not None:
            loaded.owned.close()


def put_documents_op(
    organization: str,
    index: str,
    records: Sequence[PutRecord],
    *,
    new_id: Callable[[], str],
    idempotency_key: str | None = None,
) -> Op[list[MutationResult]]:
    """Send text documents in batches and other documents alone, preserving input order.

    Every request has its own idempotency key: ``idempotency_key`` numbered by
    the request's position, so a repeated write sends the same keys. A
    document that travels alone and fails its precondition gets a result with
    an error, as it would in a batch, rather than stopping the write.
    """
    plan = plan_batches(records)
    committed: list[MutationResult] = []
    for position, step in enumerate(plan):
        key = f"{idempotency_key}-{position}" if idempotency_key else new_id()
        try:
            if isinstance(step, BatchChunk):
                response = yield Call(
                    put_objects,
                    (organization, index),
                    {
                        "body": File(payload=BytesIO(step.ndjson)),
                        "idempotency_key": build.idempotency_key(key),
                    },
                )
                committed.extend(_mutation_results(response, len(step.records)))
            else:
                record = step.record
                try:
                    result = yield from put_document_op(
                        organization,
                        index,
                        record.key,
                        record.content,
                        new_id=new_id,
                        metadata=record.metadata,
                        if_match=record.if_match,
                        if_none_match=record.if_none_match,
                        idempotency_key=key,
                    )
                except PreconditionFailedError as exc:
                    result = MutationResult(
                        key=record.key,
                        error=DocumentError(code=exc.code, reason=exc.reason, message=exc.message),
                    )
                committed.append(result)
        except GrepvineError as exc:
            if not committed:
                raise
            pending = [k for later in plan[position + 1 :] for k in later.keys]
            raise PartialBatchError(
                committed=committed,
                failed_keys=step.keys,
                pending_keys=pending,
                cause=exc,
            ) from exc
    return committed


def delete_document_op(
    organization: str,
    index: str,
    key: str,
    *,
    new_id: Callable[[], str],
    if_match: str | None = None,
    idempotency_key: str | None = None,
) -> Op[MutationResult]:
    check_key(key)
    build.check_preconditions(if_match, False)
    response = yield Call(
        delete_document,
        (organization, index, key),
        {
            "idempotency_key": build.idempotency_key(idempotency_key or new_id()),
            "if_match": UNSET if if_match is None else if_match,
        },
    )
    return _mutation_result(response)


def delete_documents_op(
    organization: str,
    index: str,
    records: Sequence[tuple[str, str | None]],
    *,
    new_id: Callable[[], str],
    idempotency_key: str | None = None,
) -> Op[list[MutationResult]]:
    chunks = [
        records[start : start + MAX_BATCH_RECORDS]
        for start in range(0, len(records), MAX_BATCH_RECORDS)
    ]
    committed: list[MutationResult] = []
    for position, chunk in enumerate(chunks):
        key = f"{idempotency_key}-{position}" if idempotency_key else new_id()
        body = api.DeleteObjectsRequest(
            objects=[
                api.DeleteObjectRecord(key=k, if_match=UNSET if m is None else m) for k, m in chunk
            ]
        )
        try:
            response = yield Call(
                delete_objects,
                (organization, index),
                {"body": body, "idempotency_key": build.idempotency_key(key)},
            )
            committed.extend(_mutation_results(response, len(chunk)))
        except GrepvineError as exc:
            if not committed:
                raise
            pending = [k for later in chunks[position + 1 :] for k, _ in later]
            raise PartialBatchError(
                committed=committed,
                failed_keys=[k for k, _ in chunk],
                pending_keys=pending,
                cause=exc,
            ) from exc
    return committed


def get_document_op(
    organization: str,
    index: str,
    key: str,
    *,
    byte_range: tuple[int | None, int | None] | None = None,
) -> Op[Document]:
    check_key(key)
    kwargs = {} if byte_range is None else {"range_": build.range_header(byte_range)}
    response = yield Call(get_document, (organization, index, key), kwargs)
    return parse.document(response, key)


def documents_listing(
    organization: str,
    index: str,
    *,
    prefix: str | None,
    delimiter: str | None,
    limit: int | None,
    page: str | None,
    page_size: int | None,
) -> PageSource[DocumentSummary]:
    if delimiter is not None and not 1 <= len(delimiter) <= 16:
        raise ValueError("delimiter must be 1 to 16 characters")
    kwargs: dict[str, Any] = {}
    if prefix:
        kwargs["prefix"] = prefix
    if delimiter:
        kwargs["delimiter"] = delimiter
    return PageSource(
        operation=list_documents,
        page_model=api.DocumentPage,
        args=(organization, index),
        kwargs=kwargs,
        page_size=resolve_page_size(page_size, limit),
        limit=limit,
        start_page=validate_page_token(page),
        parse_item=lambda item: from_api(DocumentSummary._from_json, item),
    )
