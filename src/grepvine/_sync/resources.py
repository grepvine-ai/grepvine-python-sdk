"""Synchronous resources: organizations, indexes, documents, API keys, account, device login."""

from __future__ import annotations

import builtins
from collections.abc import Callable, Iterable, Mapping, Sequence
from typing import TYPE_CHECKING, Any, Literal, overload
from uuid import UUID

from grepvine._core import ops
from grepvine._core.batching import (
    Content,
    DeleteInput,
    DocumentInput,
    normalize_delete_inputs,
    normalize_put_inputs,
)
from grepvine._core.handles import IndexFields
from grepvine._core.metadata import MetadataInput
from grepvine._core.paths import parse_index_ref
from grepvine._sync.paginator import Paginator
from grepvine.models import (
    APIKey,
    APIKeyCreated,
    DeviceAuthorization,
    Document,
    DocumentSummary,
    IndexData,
    Member,
    MutationResult,
    Organization,
    SearchResult,
    User,
)

if TYPE_CHECKING:
    from grepvine._sync.client import Client

DEFAULT_WAIT_TIMEOUT = 300.0


class Organizations:
    """The organizations the caller belongs to."""

    def __init__(self, client: Client) -> None:
        self._client = client

    def list(
        self, *, limit: int | None = None, page: str | None = None, page_size: int | None = None
    ) -> Paginator[Organization]:
        """Every organization, or at most ``limit`` of them, starting at ``page`` when given."""
        source = ops.organizations_listing(limit=limit, page=page, page_size=page_size)
        return Paginator(self._client, source)

    def get(self, name: str) -> Organization:
        """One organization by name."""
        return self._client._run(ops.get_organization_op(name))

    def create(self, name: str) -> Organization:
        """Create an organization; the caller becomes its owner.

        Organizations and user accounts share one namespace, so the name must
        not be taken by either. A name that is taken raises
        :class:`~grepvine.ConflictError`.
        """
        return self._client._run(ops.create_organization_op(name))

    def delete(self, name: str) -> None:
        """Start deleting an organization and its indexes. Needs the owner role."""
        self._client._run(ops.delete_organization_op(name))

    def transfer_ownership(self, name: str, user: str) -> None:
        """Make ``user``, already a member, the owner of the organization.

        Needs the owner role; the previous owner stays on as an admin.
        """
        self._client._run(ops.transfer_ownership_op(name, user))

    def members(self, organization: str) -> Members:
        """The members of an organization."""
        return Members(self._client, organization)


class Members:
    """The members of one organization and their roles."""

    def __init__(self, client: Client, organization: str) -> None:
        self._client = client
        self._organization = organization

    def list(
        self, *, limit: int | None = None, page: str | None = None, page_size: int | None = None
    ) -> Paginator[Member]:
        """Every member, or at most ``limit`` of them, starting at ``page`` when given."""
        source = ops.members_listing(
            self._organization, limit=limit, page=page, page_size=page_size
        )
        return Paginator(self._client, source)

    def add(self, user: str, role: str) -> Member:
        """Add the user named ``user`` with ``role``: ``"admin"``, ``"developer"`` or ``"reader"``.

        Needs the admin or owner role.
        """
        return self._client._run(ops.add_member_op(self._organization, user, role))

    def update(self, user: str, role: str) -> Member:
        """Change a member's role to ``"admin"``, ``"developer"`` or ``"reader"``.

        Use :meth:`Organizations.transfer_ownership` to change the owner.
        """
        return self._client._run(ops.update_member_op(self._organization, user, role))

    def remove(self, user: str) -> None:
        """Remove a member from the organization."""
        self._client._run(ops.remove_member_op(self._organization, user))

    def __repr__(self) -> str:
        return f"<Members {self._organization}>"


class APIKeys:
    """The API keys of the signed-in user."""

    def __init__(self, client: Client) -> None:
        self._client = client

    def list(
        self, *, limit: int | None = None, page: str | None = None, page_size: int | None = None
    ) -> Paginator[APIKey]:
        """Every API key, revoked ones included, or at most ``limit`` of them."""
        source = ops.api_keys_listing(limit=limit, page=page, page_size=page_size)
        return Paginator(self._client, source)

    def create(self, name: str) -> APIKeyCreated:
        """Issue a new API key named ``name`` (1 to 128 characters).

        The secret is in the result's ``key`` and is not shown again.
        """
        return self._client._run(ops.create_api_key_op(name))

    def revoke(self, key_id: str | UUID) -> None:
        """Revoke the API key with this ``id``; requests that use it fail from then on."""
        self._client._run(ops.revoke_api_key_op(key_id))


class Account:
    """Registration, sign-in and the signed-in user's account.

    :meth:`register` and :meth:`login` start a session that the client then
    uses in place of its API key, until :meth:`logout` ends it.
    """

    def __init__(self, client: Client) -> None:
        self._client = client

    def register(self, name: str, email: str, password: str) -> User:
        """Create a user account and sign in to it.

        ``name`` is the username, which user accounts and organizations share;
        ``password`` is at least 12 characters. A taken username or email
        address raises :class:`~grepvine.ConflictError` with code
        ``"username_taken"`` or ``"email_taken"``.
        """
        return self._client._run(ops.register_op(name, email, password))

    def username_available(self, name: str) -> bool:
        """Whether ``name`` is free for a new account or organization."""
        return self._client._run(ops.username_available_op(name))

    def login(self, identifier: str, password: str) -> User:
        """Sign in with a username or email address and a password.

        The client keeps the session and sends it, with its CSRF token, on
        every later request instead of the API key. Wrong credentials raise
        :class:`~grepvine.AuthenticationError`.
        """
        return self._client._run(ops.login_op(identifier, password))

    def logout(self) -> None:
        """End the session and stop sending it.

        With an API key this changes nothing; use :meth:`APIKeys.revoke` to revoke a key.
        """
        self._client._run(ops.logout_op())

    def me(self) -> User:
        """The user the client acts for."""
        return self._client._run(ops.me_op())

    def change_password(self, current_password: str, new_password: str) -> None:
        """Change the signed-in user's password; the new one is at least 12 characters."""
        self._client._run(ops.change_password_op(current_password, new_password))


class DeviceLogin:
    """Issuing an API key to a device, such as a command-line tool, once a user approves it.

    The device calls :meth:`start` and shows the user the verification URL and
    code, then polls with :meth:`poll` until the user approves or denies it
    from a signed-in session with :meth:`approve` or :meth:`deny`.
    :meth:`authorize` does the device's part in one call.
    """

    def __init__(self, client: Client) -> None:
        self._client = client

    def start(self, api_key_name: str) -> DeviceAuthorization:
        """Start a device login for a new API key named ``api_key_name``. Needs no credentials."""
        return self._client._run(ops.start_device_login_op(api_key_name))

    def poll(self, device_code: str) -> APIKeyCreated | None:
        """The issued API key, or None while the user has not decided yet.

        Polling more often than the authorization's ``interval`` raises
        :class:`~grepvine.InvalidRequestError` with code ``"slow_down"``; a
        denied login raises it with ``"access_denied"``, and an expired one
        with ``"expired_token"``.
        """
        return self._client._run(ops.poll_device_login_op(device_code))

    def approve(self, user_code: str) -> None:
        """Approve the device login showing ``user_code``, issuing its key to the signed-in user."""
        self._client._run(ops.approve_device_login_op(user_code))

    def deny(self, user_code: str) -> None:
        """Deny the device login showing ``user_code``."""
        self._client._run(ops.deny_device_login_op(user_code))

    def authorize(
        self,
        api_key_name: str,
        *,
        on_code: Callable[[DeviceAuthorization], Any],
        timeout: float | None = None,
    ) -> APIKeyCreated:
        """Start a device login, report it to ``on_code``, and wait for the key.

        ``on_code`` receives the :class:`~grepvine.models.DeviceAuthorization`
        to show the user. Polling follows the service's interval. A denied or
        expired login raises :class:`~grepvine.InvalidRequestError`; one
        that is not approved within ``timeout`` seconds, or before it expires,
        raises :class:`TimeoutError`. Pass the result's ``key`` to
        :meth:`Client.configure <grepvine.Client.configure>` to use it.
        """
        return self._client._run(
            ops.authorize_device_op(api_key_name, on_code=on_code, timeout=timeout)
        )


class Indexes:
    """The indexes of an organization. Indexes are referenced as ``"organization/index"``."""

    def __init__(self, client: Client) -> None:
        self._client = client

    def list(
        self,
        organization: str,
        *,
        prefix: str | None = None,
        limit: int | None = None,
        page: str | None = None,
        page_size: int | None = None,
    ) -> Paginator[Index]:
        """Every index of the organization, or at most ``limit`` of them.

        With ``prefix``, only the indexes whose names start with it, in any case. A ``page``
        token continues only a listing with the same ``prefix``.
        """
        source = ops.indexes_listing(
            organization, prefix=prefix, limit=limit, page=page, page_size=page_size
        )
        return Paginator(self._client, source.map(lambda data: Index(data, self._client)))

    def get(self, ref: str) -> Index:
        """The index ``"organization/index"``."""
        organization, index = parse_index_ref(ref)
        return Index(self._client._run(ops.get_index_op(organization, index)), self._client)

    def create(
        self,
        ref: str,
        *,
        description: str | None = None,
        tags: Mapping[str, str] | None = None,
        exist_ok: bool = False,
        wait: bool = False,
        timeout: float | None = DEFAULT_WAIT_TIMEOUT,
    ) -> Index:
        """Create the index ``"organization/index"``.

        ``description`` is Markdown saying what the index holds. ``tags`` are
        key/value labels, for example the commit the index was synced from.
        With ``exist_ok`` an index that already exists is returned as it is,
        its description and tags untouched, instead of raising
        :class:`~grepvine.errors.ConflictError`. With ``wait`` the call
        returns once the index is ready, as :meth:`Index.wait_until_ready`
        describes, waiting at most ``timeout`` seconds.
        """
        organization, index = parse_index_ref(ref)
        handle = Index(
            self._client._run(
                ops.create_index_op(
                    organization,
                    index,
                    description=description,
                    tags=tags,
                    exist_ok=exist_ok,
                )
            ),
            self._client,
        )
        return handle.wait_until_ready(timeout=timeout) if wait else handle

    def update(
        self,
        ref: str,
        *,
        description: str | None = None,
        tags: Mapping[str, str | None] | None = None,
    ) -> Index:
        """Change the description or the tags of the index ``"organization/index"``.

        ``description`` replaces the current one; an empty string clears it.
        ``tags`` is merged into the current tags: every key given is set, a
        key given as ``None`` is removed, and keys not mentioned stay as they
        are. An argument left out leaves that field unchanged; at least one
        is needed. Needs the admin or owner role.
        """
        organization, index = parse_index_ref(ref)
        return Index(
            self._client._run(
                ops.update_index_op(organization, index, description=description, tags=tags)
            ),
            self._client,
        )

    def delete(self, ref: str) -> None:
        """Start deleting the index. Deletion completes in the background."""
        organization, index = parse_index_ref(ref)
        self._client._run(ops.delete_index_op(organization, index))

    def exists(self, ref: str) -> bool:
        """Whether the index exists and is visible to this API key."""
        organization, index = parse_index_ref(ref)
        return self._client._run(ops.index_exists_op(organization, index))


class Index(IndexFields):
    """An index and the operations on it."""

    def __init__(self, data: IndexData, client: Client) -> None:
        self._data = data
        self._client = client

    @property
    def documents(self) -> Documents:
        """The documents stored in this index."""
        return Documents(self._client, self.organization, self.name)

    def search(
        self,
        pattern: str,
        *,
        regex: bool = True,
        case_sensitive: bool = True,
        whole_word: bool = False,
        multiline: bool = False,
        filter: str | None = None,
        filters: Sequence[str] | None = None,
        lines_before: int = 0,
        lines_after: int = 0,
        limit: int | None = None,
        page: str | None = None,
        page_size: int | None = None,
    ) -> Paginator[SearchResult]:
        """Search the index for ``pattern``.

        ``pattern`` is a regular expression unless ``regex`` is False. Matching
        is case sensitive unless ``case_sensitive`` is False. ``whole_word``
        needs ``regex=False``. With ``multiline`` a match may span lines.
        ``filter`` (one expression) or ``filters`` (several, joined with AND)
        restrict results by document metadata such as ``path``. ``lines_before``
        and ``lines_after`` return up to 20 context lines with each result.
        """
        source = ops.search_listing(
            self.organization,
            self.name,
            pattern,
            regex=regex,
            case_sensitive=case_sensitive,
            whole_word=whole_word,
            multiline=multiline,
            filter=filter,
            filters=filters,
            lines_before=lines_before,
            lines_after=lines_after,
            limit=limit,
            page=page,
            page_size=page_size,
        )
        return Paginator(self._client, source)

    def delete(self) -> None:
        """Start deleting this index."""
        self._client.indexes.delete(self.ref)

    def exists(self) -> bool:
        """Whether this index still exists."""
        return self._client.indexes.exists(self.ref)

    def refresh(self) -> Index:
        """A new handle with the index's current counters and state."""
        return self._client.indexes.get(self.ref)

    def wait_until_ready(
        self, *, timeout: float | None = DEFAULT_WAIT_TIMEOUT, interval: float = 1.0
    ) -> Index:
        """Wait until the index is ready and return a handle with its current state.

        The index is read every ``interval`` seconds. An index that is not
        ready within ``timeout`` seconds raises :class:`TimeoutError`
        (``None`` waits as long as it takes), and one that is being deleted
        raises :class:`~grepvine.GrepvineError`.
        """
        data = self._client._run(
            ops.wait_until_ready_op(
                self.organization, self.name, timeout=timeout, interval=interval
            )
        )
        return Index(data, self._client)

    def update(
        self,
        *,
        description: str | None = None,
        tags: Mapping[str, str | None] | None = None,
    ) -> Index:
        """Change this index's description or tags and return a handle carrying them.

        ``tags`` is merged as :meth:`Indexes.update` describes: a key given as
        ``None`` is removed and keys not mentioned stay. Handles are snapshots,
        so this one keeps the old description and tags.
        """
        return self._client.indexes.update(self.ref, description=description, tags=tags)

    def set_tags(self, tags: Mapping[str, str]) -> Index:
        """Set these tags, keeping every other tag; the same as ``update(tags=tags)``."""
        return self.update(tags=tags)

    def remove_tags(self, *keys: str) -> Index:
        """Remove these tags; the same as ``update(tags={key: None for key in keys})``."""
        return self.update(tags=dict.fromkeys(keys))


class Documents:
    """The documents of one index."""

    def __init__(self, client: Client, organization: str, index: str) -> None:
        self._client = client
        self._organization = organization
        self._index = index

    @overload
    def put(
        self,
        key: str,
        content: Content,
        *,
        metadata: MetadataInput | None = None,
        if_match: str | None = None,
        if_none_match: bool = False,
        idempotency_key: str | None = None,
    ) -> MutationResult: ...

    @overload
    def put(
        self,
        documents: Iterable[DocumentInput | Mapping[str, Any]],
        /,
        *,
        idempotency_key: str | None = None,
    ) -> builtins.list[MutationResult]: ...

    def put(
        self,
        key: str | Iterable[DocumentInput | Mapping[str, Any]],
        content: Content | None = None,
        *,
        metadata: MetadataInput | None = None,
        if_match: str | None = None,
        if_none_match: bool = False,
        idempotency_key: str | None = None,
    ) -> MutationResult | builtins.list[MutationResult]:
        """Store one document, or a list of ``{"key", "content", ...}`` documents.

        Content may be bytes, text, a path, or a binary file object. The SDK
        records ``path`` and ``size`` metadata (and ``mtime`` for a path) so
        filters work; ``metadata`` adds or overrides fields.

        The list form sends text documents in batches and any other document
        on its own, and returns one result per document in input order. Each
        document is stored on its own: one whose ``if_match`` or
        ``if_none_match`` condition fails is left unchanged and its result
        carries an ``error`` instead of raising, while the others are stored.
        See :class:`~grepvine.errors.PartialBatchError` for what happens
        when a request fails after earlier ones succeeded.
        """
        new_id = self._client._state.new_id
        if isinstance(key, str):
            if content is None:
                raise TypeError("put() needs content when storing a single document")
            return self._client._run(
                ops.put_document_op(
                    self._organization,
                    self._index,
                    key,
                    content,
                    new_id=new_id,
                    metadata=metadata,
                    if_match=if_match,
                    if_none_match=if_none_match,
                    idempotency_key=idempotency_key,
                )
            )
        if content is not None or metadata is not None or if_match is not None or if_none_match:
            raise TypeError("in the list form, give content and options inside each document")
        records = normalize_put_inputs(key)
        if not records:
            return []
        return self._client._run(
            ops.put_documents_op(
                self._organization,
                self._index,
                records,
                new_id=new_id,
                idempotency_key=idempotency_key,
            )
        )

    @overload
    def get(
        self,
        key: str,
        *,
        mode: Literal["rb"] = "rb",
        encoding: str = "utf-8",
        range: tuple[int | None, int | None] | None = None,
    ) -> bytes: ...

    @overload
    def get(
        self,
        key: str,
        *,
        mode: Literal["r"],
        encoding: str = "utf-8",
        range: tuple[int | None, int | None] | None = None,
    ) -> str: ...

    def get(
        self,
        key: str,
        *,
        mode: Literal["rb", "r"] = "rb",
        encoding: str = "utf-8",
        range: tuple[int | None, int | None] | None = None,
    ) -> bytes | str:
        """The content of a document: bytes with ``mode="rb"``, text with ``mode="r"``.

        ``range=(start, end)`` reads only those bytes (inclusive); either bound
        may be None. Use :meth:`fetch` for the revision and metadata too.
        """
        if mode not in ("rb", "r"):
            raise ValueError("mode must be 'rb' or 'r'")
        document = self.fetch(key, range=range)
        return document.content if mode == "rb" else document.content.decode(encoding)

    def fetch(self, key: str, *, range: tuple[int | None, int | None] | None = None) -> Document:
        """A document with its content, revision, and metadata."""
        return self._client._run(
            ops.get_document_op(self._organization, self._index, key, byte_range=range)
        )

    def list(
        self,
        *,
        prefix: str | None = None,
        delimiter: str | None = None,
        limit: int | None = None,
        page: str | None = None,
        page_size: int | None = None,
    ) -> Paginator[DocumentSummary]:
        """The documents of the index, optionally under ``prefix``.

        With ``delimiter`` (usually ``"/"``), documents that share the text up
        to the next delimiter are folded into ``common_prefixes`` on each page.
        """
        source = ops.documents_listing(
            self._organization,
            self._index,
            prefix=prefix,
            delimiter=delimiter,
            limit=limit,
            page=page,
            page_size=page_size,
        )
        return Paginator(self._client, source)

    @overload
    def delete(  # type: ignore[overload-overlap]
        self, key: str, *, if_match: str | None = None, idempotency_key: str | None = None
    ) -> MutationResult: ...

    @overload
    def delete(
        self,
        keys: Iterable[str | DeleteInput | Mapping[str, Any]],
        /,
        *,
        idempotency_key: str | None = None,
    ) -> builtins.list[MutationResult]: ...

    def delete(
        self,
        key: str | Iterable[str | DeleteInput | Mapping[str, Any]],
        *,
        if_match: str | None = None,
        idempotency_key: str | None = None,
    ) -> MutationResult | builtins.list[MutationResult]:
        """Delete one document by key, or a list of keys (or ``{"key", "if_match"}`` mappings).

        Deleting one missing document raises :class:`~grepvine.errors.NotFoundError`.
        The list form returns one result per key in input order and deletes
        each document on its own: a missing document, or one whose
        ``if_match`` fails, is reported by its result's ``error`` (code
        ``"not_found"`` or ``"precondition_failed"``) while the others are
        deleted.
        """
        new_id = self._client._state.new_id
        if isinstance(key, str):
            return self._client._run(
                ops.delete_document_op(
                    self._organization,
                    self._index,
                    key,
                    new_id=new_id,
                    if_match=if_match,
                    idempotency_key=idempotency_key,
                )
            )
        if if_match is not None:
            raise TypeError("in the list form, give if_match inside each mapping")
        records = normalize_delete_inputs(key)
        if not records:
            return []
        return self._client._run(
            ops.delete_documents_op(
                self._organization,
                self._index,
                records,
                new_id=new_id,
                idempotency_key=idempotency_key,
            )
        )

    def __repr__(self) -> str:
        return f"<Documents {self._organization}/{self._index}>"
