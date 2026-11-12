"""Resource classes for every API operation, one method per operation, and the scoped classes."""

from __future__ import annotations

import builtins
from collections.abc import AsyncIterator, Iterator, Mapping
from typing import Any, Literal, TypeVar, cast

from ... import _retry
from ...errors import NotFoundError, OperationFailedError, WaitTimeoutError
from ..client import Client
from ..types import File
from ..models.add_member_request import AddMemberRequest
from ..models.add_member_request_role import AddMemberRequestRole
from ..models.api_key import APIKey
from ..models.api_key_created import APIKeyCreated
from ..models.api_key_page import APIKeyPage
from ..models.auth_options import AuthOptions
from ..models.change_password_request import ChangePasswordRequest
from ..models.connection_page import ConnectionPage
from ..models.create_api_key_request import CreateAPIKeyRequest
from ..models.create_index_request import CreateIndexRequest
from ..models.create_organization_request import CreateOrganizationRequest
from ..models.delete_object_record import DeleteObjectRecord
from ..models.delete_objects_request import DeleteObjectsRequest
from ..models.device_approval_request import DeviceApprovalRequest
from ..models.device_authorization import DeviceAuthorization
from ..models.device_authorization_request import DeviceAuthorizationRequest
from ..models.device_decision_request import DeviceDecisionRequest
from ..models.device_token_request import DeviceTokenRequest
from ..models.document_page import DocumentPage
from ..models.index import Index
from ..models.index_page import IndexPage
from ..models.index_summary import IndexSummary
from ..models.index_tag_changes import IndexTagChanges
from ..models.index_tags import IndexTags
from ..models.invitation_check_request import InvitationCheckRequest
from ..models.invitation_preview import InvitationPreview
from ..models.key_scope import KeyScope
from ..models.login_request import LoginRequest
from ..models.member import Member
from ..models.member_page import MemberPage
from ..models.metadata import Metadata
from ..models.mutation_batch_result import MutationBatchResult
from ..models.mutation_result import MutationResult
from ..models.organization import Organization
from ..models.organization_page import OrganizationPage
from ..models.pending_device_authorization import PendingDeviceAuthorization
from ..models.permission import Permission
from ..models.put_document_form import PutDocumentForm
from ..models.put_document_if_none_match import PutDocumentIfNoneMatch
from ..models.query_page import QueryPage
from ..models.query_request import QueryRequest
from ..models.query_request_mode import QueryRequestMode
from ..models.query_result import QueryResult
from ..models.register_request import RegisterRequest
from ..models.tagged_boolean_metadata_value import TaggedBooleanMetadataValue
from ..models.tagged_integer_metadata_value import TaggedIntegerMetadataValue
from ..models.tagged_number_metadata_value import TaggedNumberMetadataValue
from ..models.tagged_string_metadata_value import TaggedStringMetadataValue
from ..models.tagged_timestamp_metadata_value import TaggedTimestampMetadataValue
from ..models.transfer_ownership_request import TransferOwnershipRequest
from ..models.update_index_request import UpdateIndexRequest
from ..models.update_member_request import UpdateMemberRequest
from ..models.update_member_request_role import UpdateMemberRequestRole
from ..models.user import User
from ..models.username_availability import UsernameAvailability
from .api_keys import create_api_key
from .api_keys import list_api_keys
from .api_keys import revoke_api_key
from .authentication import change_password
from .authentication import check_invitation
from .authentication import get_auth_options
from .authentication import get_current_user
from .authentication import get_username_availability
from .authentication import login
from .authentication import logout
from .authentication import register_user
from .connections import list_connections
from .connections import revoke_connection
from .device_login import approve_device_authorization
from .device_login import deny_device_authorization
from .device_login import get_device_authorization
from .device_login import poll_device_token
from .device_login import start_device_authorization
from .indexes import create_index
from .indexes import delete_index
from .indexes import get_index
from .indexes import list_indexes
from .indexes import update_index
from .objects import delete_document
from .objects import delete_objects
from .objects import get_document
from .objects import list_documents
from .objects import put_document
from .objects import put_objects
from .organizations import add_organization_member
from .organizations import create_organization
from .organizations import delete_organization
from .organizations import get_organization
from .organizations import list_organization_members
from .organizations import list_organizations
from .organizations import remove_organization_member
from .organizations import transfer_organization_ownership
from .organizations import update_organization_member
from .search import query_index
from uuid import UUID
import datetime

_M = TypeVar("_M")


def _model(model: type[_M], value: Any) -> _M:
    """``value`` as ``model``: a mapping is decoded, a model is kept."""
    return cast(Any, model).from_dict(value) if isinstance(value, Mapping) else value


def _pages(call: Any, kwargs: dict[str, Any]) -> Iterator[Any]:
    while True:
        page = call(**kwargs).parsed
        yield from page.results
        if not page.pagination.has_next:
            return
        kwargs = {**kwargs, "page": page.pagination.next_page_id}


async def _async_pages(call: Any, kwargs: dict[str, Any]) -> AsyncIterator[Any]:
    while True:
        page = (await call(**kwargs)).parsed
        for item in page.results:
            yield item
        if not page.pagination.has_next:
            return
        kwargs = {**kwargs, "page": page.pagination.next_page_id}


class _Pending:
    """Work the service finishes in the background, and how to wait for it."""

    _done: tuple[str, ...] = ()
    _gone = False
    _failed: tuple[str, ...] = ()

    def __init__(self, result: Any, poll: Any, kwargs: dict[str, Any], what: str) -> None:
        self.result = result
        self._poll = poll
        self._kwargs = kwargs
        self._what = what

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self._what!r})"

    def _finished(self, found: Any, waited: float, timeout: float | None) -> bool:
        state = str(found.state)
        if not self._gone and state in self._done:
            return True
        if state in self._failed:
            raise OperationFailedError(target=self._what, state=state)
        if timeout is not None and waited >= timeout:
            raise WaitTimeoutError(target=self._what, state=state, timeout=timeout)
        return False

    def _wait(self, timeout: float | None, interval: float) -> Any:
        started = _retry.monotonic()
        while True:
            try:
                found = self._poll(**self._kwargs).parsed
            except NotFoundError:
                if self._gone:
                    return None
                raise
            if self._finished(found, _retry.monotonic() - started, timeout):
                return found
            _retry.sleep(interval)

    async def _async_wait(self, timeout: float | None, interval: float) -> Any:
        started = _retry.monotonic()
        while True:
            try:
                found = (await self._poll(**self._kwargs)).parsed
            except NotFoundError:
                if self._gone:
                    return None
                raise
            if self._finished(found, _retry.monotonic() - started, timeout):
                return found
            await _retry.async_sleep(interval)


class IndexCreation(_Pending):
    """An index being created. ``result`` is the index as the service answered; ``wait()`` waits until it can be used."""

    result: Index
    _done = ("ready",)
    _failed = (
        "deleting",
        "delete_failed",
        "recreate_required",
    )

    def wait(self, timeout: float | None = 300.0, *, interval: float = 1.0) -> Index:
        """Wait until the index is ready.

        Args:
            timeout: Seconds to wait before giving up; ``None`` waits without a limit.
            interval: Seconds between reads.

        Returns:
            The index, ready to use.

        Raises:
            grepvine.WaitTimeoutError: The work was not done within ``timeout`` seconds. It goes
                on in the service; wait again to keep waiting.
            grepvine.OperationFailedError: The index reached a state it will not leave
                by itself: ``deleting``, ``delete_failed``, ``recreate_required``.
            grepvine.APIError: Reading the index failed.
        """
        return cast(Index, self._wait(timeout, interval))


class AsyncIndexCreation(_Pending):
    """An index being created. ``result`` is the index as the service answered; ``wait()`` waits until it can be used."""

    result: Index
    _done = ("ready",)
    _failed = (
        "deleting",
        "delete_failed",
        "recreate_required",
    )

    async def wait(self, timeout: float | None = 300.0, *, interval: float = 1.0) -> Index:
        """Wait until the index is ready.

        Args:
            timeout: Seconds to wait before giving up; ``None`` waits without a limit.
            interval: Seconds between reads.

        Returns:
            The index, ready to use.

        Raises:
            grepvine.WaitTimeoutError: The work was not done within ``timeout`` seconds. It goes
                on in the service; wait again to keep waiting.
            grepvine.OperationFailedError: The index reached a state it will not leave
                by itself: ``deleting``, ``delete_failed``, ``recreate_required``.
            grepvine.APIError: Reading the index failed.
        """
        return cast(Index, await self._async_wait(timeout, interval))


class IndexDeletion(_Pending):
    """An index being deleted. ``wait()`` waits until it is gone and its name can be used again."""

    result: None
    _gone = True
    _failed = ("delete_failed",)

    def wait(self, timeout: float | None = 300.0, *, interval: float = 1.0) -> None:
        """Wait until the index no longer exists.

        Args:
            timeout: Seconds to wait before giving up; ``None`` waits without a limit.
            interval: Seconds between reads.

        Returns:
            None, once the index is gone.

        Raises:
            grepvine.WaitTimeoutError: The work was not done within ``timeout`` seconds. It goes
                on in the service; wait again to keep waiting.
            grepvine.OperationFailedError: The index reached a state it will not leave
                by itself: ``delete_failed``.
            grepvine.APIError: Reading the index failed.
        """
        self._wait(timeout, interval)


class AsyncIndexDeletion(_Pending):
    """An index being deleted. ``wait()`` waits until it is gone and its name can be used again."""

    result: None
    _gone = True
    _failed = ("delete_failed",)

    async def wait(self, timeout: float | None = 300.0, *, interval: float = 1.0) -> None:
        """Wait until the index no longer exists.

        Args:
            timeout: Seconds to wait before giving up; ``None`` waits without a limit.
            interval: Seconds between reads.

        Returns:
            None, once the index is gone.

        Raises:
            grepvine.WaitTimeoutError: The work was not done within ``timeout`` seconds. It goes
                on in the service; wait again to keep waiting.
            grepvine.OperationFailedError: The index reached a state it will not leave
                by itself: ``delete_failed``.
            grepvine.APIError: Reading the index failed.
        """
        await self._async_wait(timeout, interval)


class Members:
    """The members of an organization and their roles."""

    def __init__(self, client: Client) -> None:
        self._client = client

    def list(
        self,
        organization: str,
        *,
        amount: int | None = None,
    ) -> Iterator[Member]:
        """List organization members: every result, page after page.

        Lists an organization's members and their roles, ordered by name. Requires the owner or admin
        role.

        Args:
            organization: An account or organization name. Accounts and organizations share one
                namespace. A name keeps the case it was created with, and any spelling that differs only in
                case refers to it; no other account or organization can take such a spelling.
            amount: Default: 50.

        Returns:
            An iterator over Member, which requests each page as it is reached.

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        kwargs["organization"] = organization
        if amount is not None:
            kwargs["amount"] = amount

        return _pages(list_organization_members.sync_detailed, kwargs)

    def list_page(
        self,
        organization: str,
        *,
        amount: int | None = None,
        page: str | None = None,
    ) -> MemberPage:
        """List organization members: one page.

        Lists an organization's members and their roles, ordered by name. Requires the owner or admin
        role.

        Args:
            organization: An account or organization name. Accounts and organizations share one
                namespace. A name keeps the case it was created with, and any spelling that differs only in
                case refers to it; no other account or organization can take such a spelling.
            amount: Default: 50.
            page: The ``pagination.next_page_id`` of the previous page; the first page without it.

        Returns:
            MemberPage

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        kwargs["organization"] = organization
        if amount is not None:
            kwargs["amount"] = amount

        if page is not None:
            kwargs["page"] = page
        response = list_organization_members.sync_detailed(**kwargs)
        return cast(MemberPage, response.parsed)

    def add(
        self,
        organization: str,
        *,
        user: str,
        role: Literal["admin", "developer", "reader"],
    ) -> Member:
        """Add an organization member

        Adds an existing account to the organization with the admin, developer or reader role. Requires
        the owner or admin role. An organization has one owner, changed only by transferring ownership.

        Args:
            organization: An account or organization name. Accounts and organizations share one
                namespace. A name keeps the case it was created with, and any spelling that differs only in
                case refers to it; no other account or organization can take such a spelling.
            user: An account or organization name. Accounts and organizations share one namespace. A
                name keeps the case it was created with, and any spelling that differs only in case refers
                to it; no other account or organization can take such a spelling.
            role: The role to grant. `owner` is granted only by transferring ownership. One of
                ``"admin"``, ``"developer"``, ``"reader"``.

        Returns:
            Member

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        kwargs["organization"] = organization
        fields: dict[str, Any] = {}
        fields["user"] = user
        fields["role"] = AddMemberRequestRole(role)
        kwargs["body"] = AddMemberRequest(**fields)

        response = add_organization_member.sync_detailed(**kwargs)
        return cast(Member, response.parsed)

    def update(
        self,
        organization: str,
        user: str,
        *,
        role: Literal["admin", "developer", "reader"],
    ) -> Member:
        """Change an organization member role

        Changes a member's role to admin, developer or reader. Requires the owner or admin role. The
        owner's role changes only by transferring ownership.

        Args:
            organization: An account or organization name. Accounts and organizations share one
                namespace. A name keeps the case it was created with, and any spelling that differs only in
                case refers to it; no other account or organization can take such a spelling.
            user: An account or organization name. Accounts and organizations share one namespace. A
                name keeps the case it was created with, and any spelling that differs only in case refers
                to it; no other account or organization can take such a spelling.
            role: The new role. `owner` is granted only by transferring ownership. One of ``"admin"``,
                ``"developer"``, ``"reader"``.

        Returns:
            Member

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        kwargs["organization"] = organization
        kwargs["user"] = user
        fields: dict[str, Any] = {}
        fields["role"] = UpdateMemberRequestRole(role)
        kwargs["body"] = UpdateMemberRequest(**fields)

        response = update_organization_member.sync_detailed(**kwargs)
        return cast(Member, response.parsed)

    def remove(
        self,
        organization: str,
        user: str,
    ) -> None:
        """Remove an organization member

        Removes a member from the organization. Requires the owner or admin role. The owner can't be
        removed; transfer ownership first.

        Args:
            organization: An account or organization name. Accounts and organizations share one
                namespace. A name keeps the case it was created with, and any spelling that differs only in
                case refers to it; no other account or organization can take such a spelling.
            user: An account or organization name. Accounts and organizations share one namespace. A
                name keeps the case it was created with, and any spelling that differs only in case refers
                to it; no other account or organization can take such a spelling.

        Returns:
            None

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        kwargs["organization"] = organization
        kwargs["user"] = user

        remove_organization_member.sync_detailed(**kwargs)


class Organizations:
    """Organizations: create, read, delete and transfer them."""

    members: Members

    def __init__(self, client: Client) -> None:
        self._client = client
        self.members = Members(client)

    def list(
        self,
        *,
        amount: int | None = None,
    ) -> Iterator[Organization]:
        """List organizations: every result, page after page.

        Lists the organizations the authenticated account belongs to, with its role in each, ordered by
        name.

        Args:
            amount: Default: 50.

        Returns:
            An iterator over Organization, which requests each page as it is reached.

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        if amount is not None:
            kwargs["amount"] = amount

        return _pages(list_organizations.sync_detailed, kwargs)

    def list_page(
        self,
        *,
        amount: int | None = None,
        page: str | None = None,
    ) -> OrganizationPage:
        """List organizations: one page.

        Lists the organizations the authenticated account belongs to, with its role in each, ordered by
        name.

        Args:
            amount: Default: 50.
            page: The ``pagination.next_page_id`` of the previous page; the first page without it.

        Returns:
            OrganizationPage

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        if amount is not None:
            kwargs["amount"] = amount

        if page is not None:
            kwargs["page"] = page
        response = list_organizations.sync_detailed(**kwargs)
        return cast(OrganizationPage, response.parsed)

    def create(
        self,
        *,
        name: str,
    ) -> Organization:
        """Create an organization

        Creates an organization owned by the authenticated account. Accounts and organizations share one
        namespace, so a 409 means an account or organization already holds the name, in any case.

        Args:
            name: An account or organization name. Accounts and organizations share one namespace. A
                name keeps the case it was created with, and any spelling that differs only in case refers
                to it; no other account or organization can take such a spelling.

        Returns:
            Organization

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        fields: dict[str, Any] = {}
        fields["name"] = name
        kwargs["body"] = CreateOrganizationRequest(**fields)

        response = create_organization.sync_detailed(**kwargs)
        return cast(Organization, response.parsed)

    def get(
        self,
        organization: str,
    ) -> Organization:
        """Get an organization

        Returns an organization the authenticated account belongs to, with its role there. It answers
        for a suspended organization too, and reports `suspended`.

        Args:
            organization: An account or organization name. Accounts and organizations share one
                namespace. A name keeps the case it was created with, and any spelling that differs only in
                case refers to it; no other account or organization can take such a spelling.

        Returns:
            Organization

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        kwargs["organization"] = organization

        response = get_organization.sync_detailed(**kwargs)
        return cast(Organization, response.parsed)

    def delete(
        self,
        organization: str,
    ) -> None:
        """Delete an organization

        Starts deleting an organization with all its indexes and documents. Only the owner can delete
        it. The deletion finishes in the background and can't be undone.

        Args:
            organization: An account or organization name. Accounts and organizations share one
                namespace. A name keeps the case it was created with, and any spelling that differs only in
                case refers to it; no other account or organization can take such a spelling.

        Returns:
            None

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        kwargs["organization"] = organization

        delete_organization.sync_detailed(**kwargs)

    def transfer_ownership(
        self,
        organization: str,
        *,
        user: str,
    ) -> None:
        """Transfer organization ownership

        Makes another member the owner. Only the owner can transfer ownership, and the previous owner
        stays a member with the admin role. The new owner must already be a member, and not one with
        time-limited access.

        Args:
            organization: An account or organization name. Accounts and organizations share one
                namespace. A name keeps the case it was created with, and any spelling that differs only in
                case refers to it; no other account or organization can take such a spelling.
            user: An account or organization name. Accounts and organizations share one namespace. A
                name keeps the case it was created with, and any spelling that differs only in case refers
                to it; no other account or organization can take such a spelling.

        Returns:
            None

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        kwargs["organization"] = organization
        fields: dict[str, Any] = {}
        fields["user"] = user
        kwargs["body"] = TransferOwnershipRequest(**fields)

        transfer_organization_ownership.sync_detailed(**kwargs)


class Indexes:
    """Indexes in an organization."""

    def __init__(self, client: Client) -> None:
        self._client = client

    def list(
        self,
        organization: str,
        *,
        amount: int | None = None,
        prefix: str | None = None,
    ) -> Iterator[IndexSummary]:
        """List indexes: every result, page after page.

        Lists the organization's indexes, ordered by name. Any member can list them.

        Args:
            organization: An account or organization name. Accounts and organizations share one
                namespace. A name keeps the case it was created with, and any spelling that differs only in
                case refers to it; no other account or organization can take such a spelling.
            amount: Default: 50.
            prefix:

        Returns:
            An iterator over IndexSummary, which requests each page as it is reached.

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        kwargs["organization"] = organization
        if amount is not None:
            kwargs["amount"] = amount
        if prefix is not None:
            kwargs["prefix"] = prefix

        return _pages(list_indexes.sync_detailed, kwargs)

    def list_page(
        self,
        organization: str,
        *,
        amount: int | None = None,
        prefix: str | None = None,
        page: str | None = None,
    ) -> IndexPage:
        """List indexes: one page.

        Lists the organization's indexes, ordered by name. Any member can list them.

        Args:
            organization: An account or organization name. Accounts and organizations share one
                namespace. A name keeps the case it was created with, and any spelling that differs only in
                case refers to it; no other account or organization can take such a spelling.
            amount: Default: 50.
            prefix:
            page: The ``pagination.next_page_id`` of the previous page; the first page without it.

        Returns:
            IndexPage

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        kwargs["organization"] = organization
        if amount is not None:
            kwargs["amount"] = amount
        if prefix is not None:
            kwargs["prefix"] = prefix

        if page is not None:
            kwargs["page"] = page
        response = list_indexes.sync_detailed(**kwargs)
        return cast(IndexPage, response.parsed)

    def create(
        self,
        organization: str,
        *,
        name: str,
        description: str | None = None,
        tags: IndexTags | Mapping[str, str] | None = None,
    ) -> IndexCreation:
        """Create an index

        Creates an empty index. Requires the owner or admin role. A new index is usually `ready` in the
        response; if it is still `creating`, read it until it is `ready`. A 409 means the organization
        already has an index with that name, in any case.

        Args:
            organization: An account or organization name. Accounts and organizations share one
                namespace. A name keeps the case it was created with, and any spelling that differs only in
                case refers to it; no other account or organization can take such a spelling.
            name: An index name, unique in its organization. A name keeps the case it was created with,
                and any spelling that differs only in case refers to it; no other index in the organization
                can take such a spelling.
            description: What the index holds, in Markdown. Empty when no description was set. Clients
                render it without raw HTML.
            tags: Key/value labels on the index, for example the commit it was synced from. At most 64
                tags. A key is 1 to 128 characters without whitespace or control characters; a value is at
                most 1,024 characters without control characters. Empty when none was set.

        Returns:
            IndexCreation: the answer as ``result``, and ``wait()`` to wait until the work is done.

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        kwargs["organization"] = organization
        fields: dict[str, Any] = {}
        fields["name"] = name
        if description is not None:
            fields["description"] = description
        if tags is not None:
            fields["tags"] = _model(IndexTags, tags)
        kwargs["body"] = CreateIndexRequest(**fields)

        response = create_index.sync_detailed(**kwargs)
        source = {**kwargs, **fields}
        polled = {
            "organization": source["organization"],
            "index": source["name"],
        }
        return IndexCreation(
            response.parsed,
            get_index.sync_detailed,
            {"client": self._client, **polled},
            "index " + "/".join(polled.values()),
        )

    def get(
        self,
        organization: str,
        index: str,
    ) -> Index:
        """Get an index

        Returns one index with its current state, document count and size, and the progress of its
        background optimization while one runs. Any member can read it.

        Args:
            organization: An account or organization name. Accounts and organizations share one
                namespace. A name keeps the case it was created with, and any spelling that differs only in
                case refers to it; no other account or organization can take such a spelling.
            index: An index name, unique in its organization. A name keeps the case it was created with,
                and any spelling that differs only in case refers to it; no other index in the organization
                can take such a spelling.

        Returns:
            Index

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        kwargs["organization"] = organization
        kwargs["index"] = index

        response = get_index.sync_detailed(**kwargs)
        return cast(Index, response.parsed)

    def update(
        self,
        organization: str,
        index: str,
        *,
        description: str | None = None,
        tags: IndexTagChanges | Mapping[str, None | str] | None = None,
    ) -> Index:
        """Update an index

        Changes the index's description or tags. A field absent from the request is left as it is. The
        name is immutable.

        Args:
            organization: An account or organization name. Accounts and organizations share one
                namespace. A name keeps the case it was created with, and any spelling that differs only in
                case refers to it; no other account or organization can take such a spelling.
            index: An index name, unique in its organization. A name keeps the case it was created with,
                and any spelling that differs only in case refers to it; no other index in the organization
                can take such a spelling.
            description: What the index holds, in Markdown. Empty when no description was set. Clients
                render it without raw HTML.
            tags: Tags to set, by key, and tags to remove, given as null. A key absent from the map is
                unchanged.

        Returns:
            Index

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        kwargs["organization"] = organization
        kwargs["index"] = index
        fields: dict[str, Any] = {}
        if description is not None:
            fields["description"] = description
        if tags is not None:
            fields["tags"] = _model(IndexTagChanges, tags)
        kwargs["body"] = UpdateIndexRequest(**fields)

        response = update_index.sync_detailed(**kwargs)
        return cast(Index, response.parsed)

    def delete(
        self,
        organization: str,
        index: str,
    ) -> IndexDeletion:
        """Delete an index

        Starts deleting an index and all its documents. Requires the owner or admin role. The index is
        `deleting` until the deletion finishes in the background, and it can't be undone.

        Args:
            organization: An account or organization name. Accounts and organizations share one
                namespace. A name keeps the case it was created with, and any spelling that differs only in
                case refers to it; no other account or organization can take such a spelling.
            index: An index name, unique in its organization. A name keeps the case it was created with,
                and any spelling that differs only in case refers to it; no other index in the organization
                can take such a spelling.

        Returns:
            IndexDeletion: the answer as ``result``, and ``wait()`` to wait until the work is done.

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        kwargs["organization"] = organization
        kwargs["index"] = index

        response = delete_index.sync_detailed(**kwargs)
        source = kwargs
        polled = {
            "organization": source["organization"],
            "index": source["index"],
        }
        return IndexDeletion(
            response.parsed,
            get_index.sync_detailed,
            {"client": self._client, **polled},
            "index " + "/".join(polled.values()),
        )


class Documents:
    """The documents of an index."""

    def __init__(self, client: Client) -> None:
        self._client = client

    def list_page(
        self,
        organization: str,
        index: str,
        *,
        amount: int | None = None,
        prefix: str | None = None,
        delimiter: str | None = None,
        page: str | None = None,
    ) -> DocumentPage:
        """List documents: one page.

        Lists documents in key byte order, with each one's revision, size, metadata and whether a search
        can match it. Narrow the listing with `prefix`, and add `delimiter` to browse keys like a
        directory tree: keys that share the part up to the next delimiter are returned once, in
        `common_prefixes`.

        Args:
            organization: An account or organization name. Accounts and organizations share one
                namespace. A name keeps the case it was created with, and any spelling that differs only in
                case refers to it; no other account or organization can take such a spelling.
            index: An index name, unique in its organization. A name keeps the case it was created with,
                and any spelling that differs only in case refers to it; no other index in the organization
                can take such a spelling.
            amount: Default: 50.
            prefix:
            delimiter:
            page: The ``pagination.next_page_id`` of the previous page; the first page without it.

        Returns:
            DocumentPage

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        kwargs["organization"] = organization
        kwargs["index"] = index
        if amount is not None:
            kwargs["amount"] = amount
        if prefix is not None:
            kwargs["prefix"] = prefix
        if delimiter is not None:
            kwargs["delimiter"] = delimiter

        if page is not None:
            kwargs["page"] = page
        response = list_documents.sync_detailed(**kwargs)
        return cast(DocumentPage, response.parsed)

    def put(
        self,
        organization: str,
        index: str,
        *,
        key: str,
        content: File,
        metadata: Metadata
        | Mapping[
            str,
            bool
            | int
            | str
            | TaggedBooleanMetadataValue
            | TaggedIntegerMetadataValue
            | TaggedNumberMetadataValue
            | TaggedStringMetadataValue
            | TaggedTimestampMetadataValue,
        ]
        | None = None,
        idempotency_key: str | None = None,
        if_match: str | None = None,
        if_none_match: Literal["*"] | None = None,
    ) -> MutationResult:
        """Store one document

        Stores one document of at most 1 GiB. Content that is valid UTF-8 and at most 100 MiB is
        searchable. Any other content, such as an image or a larger file, is stored, listed, and served
        by the document endpoints but is never matched by a search. The `searchable` field of a listing
        reports which applies.

        Args:
            organization: An account or organization name. Accounts and organizations share one
                namespace. A name keeps the case it was created with, and any spelling that differs only in
                case refers to it; no other account or organization can take such a spelling.
            index: An index name, unique in its organization. A name keeps the case it was created with,
                and any spelling that differs only in case refers to it; no other index in the organization
                can take such a spelling.
            key: The document's key: a UTF-8, POSIX-style path of at most 1,024 bytes, with no empty,
                `.` or `..` components. Storing a key that exists replaces that document.
            content: The document bytes, at most 1 GiB. Valid UTF-8 of at most 100 MiB is searchable;
                other content is stored without being searchable.
            metadata: Document metadata as a request sends it. Values are plain or tagged.
            idempotency_key:
            if_match:
            if_none_match: One of ``"*"``.

        Returns:
            MutationResult

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        kwargs["organization"] = organization
        kwargs["index"] = index
        if idempotency_key is not None:
            kwargs["idempotency_key"] = idempotency_key
        if if_match is not None:
            kwargs["if_match"] = if_match
        if if_none_match is not None:
            kwargs["if_none_match"] = PutDocumentIfNoneMatch(if_none_match)
        fields: dict[str, Any] = {}
        fields["key"] = key
        fields["content"] = content
        if metadata is not None:
            fields["metadata"] = _model(Metadata, metadata)
        kwargs["body"] = PutDocumentForm(**fields)

        response = put_document.sync_detailed(**kwargs)
        return cast(MutationResult, response.parsed)

    def get(
        self,
        organization: str,
        index: str,
        key: str,
        *,
        range: str | None = None,
    ) -> File:
        """Get a document

        Returns a document's content exactly as it was stored, its revision in the ETag header and its
        metadata in the X-Grepvine-Metadata header. Send a Range header to read one byte range; the
        response is then 206, or 416 when the range lies outside the document.

        Args:
            organization: An account or organization name. Accounts and organizations share one
                namespace. A name keeps the case it was created with, and any spelling that differs only in
                case refers to it; no other account or organization can take such a spelling.
            index: An index name, unique in its organization. A name keeps the case it was created with,
                and any spelling that differs only in case refers to it; no other index in the organization
                can take such a spelling.
            key:
            range:

        Returns:
            File

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        kwargs["organization"] = organization
        kwargs["index"] = index
        kwargs["key"] = key
        if range is not None:
            kwargs["range_"] = range

        response = get_document.sync_detailed(**kwargs)
        return cast(File, response.parsed)

    def delete(
        self,
        organization: str,
        index: str,
        key: str,
        *,
        idempotency_key: str | None = None,
        if_match: str | None = None,
    ) -> MutationResult:
        """Delete one document

        Deletes one document. Send If-Match with a revision to delete it only if it still has that
        revision. Retrying with the same Idempotency-Key returns the original result. Once acknowledged,
        the document no longer matches any search.

        Args:
            organization: An account or organization name. Accounts and organizations share one
                namespace. A name keeps the case it was created with, and any spelling that differs only in
                case refers to it; no other account or organization can take such a spelling.
            index: An index name, unique in its organization. A name keeps the case it was created with,
                and any spelling that differs only in case refers to it; no other index in the organization
                can take such a spelling.
            key:
            idempotency_key:
            if_match:

        Returns:
            MutationResult

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        kwargs["organization"] = organization
        kwargs["index"] = index
        kwargs["key"] = key
        if idempotency_key is not None:
            kwargs["idempotency_key"] = idempotency_key
        if if_match is not None:
            kwargs["if_match"] = if_match

        response = delete_document.sync_detailed(**kwargs)
        return cast(MutationResult, response.parsed)

    def put_batch(
        self,
        organization: str,
        index: str,
        *,
        body: File,
        idempotency_key: str | None = None,
    ) -> MutationBatchResult:
        """Store a batch of documents

        Stores up to 2,048 documents. Each document is stored on its own: a document whose precondition
        fails is not stored, the others are, and the result of each document says which happened.
        Retrying
        with the same Idempotency-Key returns the same results and stores any document an interrupted
        attempt did not reach. Batch content is text carried as JSON strings, so every document stored
        this
        way is searchable. Store binary content, or a document over 16 MiB, with the
        single-document endpoint. The body may be sent with `Content-Encoding: gzip`; the service
        decodes it
        before applying the limits below, and answers any other content encoding with 415
        `unsupported_content_encoding`.

        Args:
            organization: An account or organization name. Accounts and organizations share one
                namespace. A name keeps the case it was created with, and any spelling that differs only in
                case refers to it; no other account or organization can take such a spelling.
            index: An index name, unique in its organization. A name keeps the case it was created with,
                and any spelling that differs only in case refers to it; no other index in the organization
                can take such a spelling.
            idempotency_key:

        Returns:
            MutationBatchResult

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        kwargs["organization"] = organization
        kwargs["index"] = index
        if idempotency_key is not None:
            kwargs["idempotency_key"] = idempotency_key
        kwargs["body"] = body

        response = put_objects.sync_detailed(**kwargs)
        return cast(MutationBatchResult, response.parsed)

    def delete_batch(
        self,
        organization: str,
        index: str,
        *,
        objects: builtins.list[DeleteObjectRecord | Mapping[str, Any]],
        idempotency_key: str | None = None,
    ) -> MutationBatchResult:
        """Delete a batch of documents

        Deletes up to 2,048 documents. Each document is deleted on its own: a document that does not
        exist or whose precondition fails is not deleted, the others are, and the result of each
        document
        says which happened. Retrying with the same Idempotency-Key returns the same results.

        Args:
            organization: An account or organization name. Accounts and organizations share one
                namespace. A name keeps the case it was created with, and any spelling that differs only in
                case refers to it; no other account or organization can take such a spelling.
            index: An index name, unique in its organization. A name keeps the case it was created with,
                and any spelling that differs only in case refers to it; no other index in the organization
                can take such a spelling.
            objects: The documents to delete, 1 to 2,048.
            idempotency_key:

        Returns:
            MutationBatchResult

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        kwargs["organization"] = organization
        kwargs["index"] = index
        if idempotency_key is not None:
            kwargs["idempotency_key"] = idempotency_key
        fields: dict[str, Any] = {}
        fields["objects"] = [_model(DeleteObjectRecord, item) for item in objects]
        kwargs["body"] = DeleteObjectsRequest(**fields)

        response = delete_objects.sync_detailed(**kwargs)
        return cast(MutationBatchResult, response.parsed)


class Search:
    """Search over the documents of an index."""

    def __init__(self, client: Client) -> None:
        self._client = client

    def query(
        self,
        organization: str,
        index: str,
        *,
        pattern: str,
        mode: Literal["regex", "literal"] | None = None,
        case_sensitive: bool | None = None,
        whole_word: bool | None = None,
        multiline: bool | None = None,
        filter: str | None = None,
        lines_before: int | None = None,
        lines_after: int | None = None,
        amount: int | None = None,
    ) -> Iterator[QueryResult]:
        """Search an index: every result, page after page.

        Searches every searchable document in the index for a regular expression or literal text, and
        returns each match with the lines it covers, sorted by key, then line, then offset. A metadata
        filter restricts the search to matching documents, and context lines can be returned around each
        result. A pattern or filter that doesn't parse is rejected with 400 and code `invalid_pattern`
        or `invalid_filter`.

        Args:
            organization: An account or organization name. Accounts and organizations share one
                namespace. A name keeps the case it was created with, and any spelling that differs only in
                case refers to it; no other account or organization can take such a spelling.
            index: An index name, unique in its organization. A name keeps the case it was created with,
                and any spelling that differs only in case refers to it; no other index in the organization
                can take such a spelling.
            pattern: What to search for: an RE2 regular expression, or literal text when `mode` is
                `literal`. Required; at most 8,192 characters of valid UTF-8.
            mode: How to read the pattern: `regex` (the default) for RE2 syntax, without backreferences
                or lookaround, or `literal` to match its bytes exactly, with no escaping needed. One of
                ``"regex"``, ``"literal"``.
            case_sensitive: Whether case must match. Defaults to true. False matches under Unicode
                simple case folding; in a regex, `(?i)` does the same for part of the pattern.
            whole_word: Match only where the characters on either side of the match aren't word
                characters: letters, digits or `_`. Defaults to false. Valid only in literal mode.
            multiline: Let a match span lines. Without it a pattern matches within one line, `^` and `$`
                mark the line's edges, and a character class never matches a line break; a pattern that
                contains a line break is rejected. With it the pattern is matched against the whole
                document, `^` and `$` still mark line edges, `\\A` and `\\z` mark the document's edges, and
                a match may contain line breaks. Default: False.
            filter: Search only the documents whose metadata matches this expression, such as `path
                STARTSWITH 'src/' AND size < 1048576`. At most 8,192 characters. Omit it to search every
                document.
            lines_before: How many lines before each result to return with it, from the same document.
                Default: 0.
            lines_after: How many lines after each result to return with it, from the same document.
                Default: 0.
            amount: Default: 50.

        Returns:
            An iterator over QueryResult, which requests each page as it is reached.

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        kwargs["organization"] = organization
        kwargs["index"] = index
        if amount is not None:
            kwargs["amount"] = amount
        fields: dict[str, Any] = {}
        fields["pattern"] = pattern
        if mode is not None:
            fields["mode"] = QueryRequestMode(mode)
        if case_sensitive is not None:
            fields["case_sensitive"] = case_sensitive
        if whole_word is not None:
            fields["whole_word"] = whole_word
        if multiline is not None:
            fields["multiline"] = multiline
        if filter is not None:
            fields["filter_"] = filter
        if lines_before is not None:
            fields["lines_before"] = lines_before
        if lines_after is not None:
            fields["lines_after"] = lines_after
        kwargs["body"] = QueryRequest(**fields)

        return _pages(query_index.sync_detailed, kwargs)

    def query_page(
        self,
        organization: str,
        index: str,
        *,
        pattern: str,
        mode: Literal["regex", "literal"] | None = None,
        case_sensitive: bool | None = None,
        whole_word: bool | None = None,
        multiline: bool | None = None,
        filter: str | None = None,
        lines_before: int | None = None,
        lines_after: int | None = None,
        amount: int | None = None,
        page: str | None = None,
    ) -> QueryPage:
        """Search an index: one page.

        Searches every searchable document in the index for a regular expression or literal text, and
        returns each match with the lines it covers, sorted by key, then line, then offset. A metadata
        filter restricts the search to matching documents, and context lines can be returned around each
        result. A pattern or filter that doesn't parse is rejected with 400 and code `invalid_pattern`
        or `invalid_filter`. Continue with `page` while `has_next` is true: a page can be empty while
        more results follow.

        Args:
            organization: An account or organization name. Accounts and organizations share one
                namespace. A name keeps the case it was created with, and any spelling that differs only in
                case refers to it; no other account or organization can take such a spelling.
            index: An index name, unique in its organization. A name keeps the case it was created with,
                and any spelling that differs only in case refers to it; no other index in the organization
                can take such a spelling.
            pattern: What to search for: an RE2 regular expression, or literal text when `mode` is
                `literal`. Required; at most 8,192 characters of valid UTF-8.
            mode: How to read the pattern: `regex` (the default) for RE2 syntax, without backreferences
                or lookaround, or `literal` to match its bytes exactly, with no escaping needed. One of
                ``"regex"``, ``"literal"``.
            case_sensitive: Whether case must match. Defaults to true. False matches under Unicode
                simple case folding; in a regex, `(?i)` does the same for part of the pattern.
            whole_word: Match only where the characters on either side of the match aren't word
                characters: letters, digits or `_`. Defaults to false. Valid only in literal mode.
            multiline: Let a match span lines. Without it a pattern matches within one line, `^` and `$`
                mark the line's edges, and a character class never matches a line break; a pattern that
                contains a line break is rejected. With it the pattern is matched against the whole
                document, `^` and `$` still mark line edges, `\\A` and `\\z` mark the document's edges, and
                a match may contain line breaks. Default: False.
            filter: Search only the documents whose metadata matches this expression, such as `path
                STARTSWITH 'src/' AND size < 1048576`. At most 8,192 characters. Omit it to search every
                document.
            lines_before: How many lines before each result to return with it, from the same document.
                Default: 0.
            lines_after: How many lines after each result to return with it, from the same document.
                Default: 0.
            amount: Default: 50.
            page: The ``pagination.next_page_id`` of the previous page; the first page without it.

        Returns:
            QueryPage

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        kwargs["organization"] = organization
        kwargs["index"] = index
        if amount is not None:
            kwargs["amount"] = amount
        fields: dict[str, Any] = {}
        fields["pattern"] = pattern
        if mode is not None:
            fields["mode"] = QueryRequestMode(mode)
        if case_sensitive is not None:
            fields["case_sensitive"] = case_sensitive
        if whole_word is not None:
            fields["whole_word"] = whole_word
        if multiline is not None:
            fields["multiline"] = multiline
        if filter is not None:
            fields["filter_"] = filter
        if lines_before is not None:
            fields["lines_before"] = lines_before
        if lines_after is not None:
            fields["lines_after"] = lines_after
        kwargs["body"] = QueryRequest(**fields)

        if page is not None:
            kwargs["page"] = page
        response = query_index.sync_detailed(**kwargs)
        return cast(QueryPage, response.parsed)


class APIKeys:
    """The API keys of the signed-in user."""

    def __init__(self, client: Client) -> None:
        self._client = client

    def list(
        self,
        *,
        amount: int | None = None,
    ) -> Iterator[APIKey]:
        """List API keys: every result, page after page.

        Lists the authenticated account's API keys, oldest first, including revoked ones. The secret key
        itself is never returned again; `prefix` tells keys apart.

        Args:
            amount: Default: 50.

        Returns:
            An iterator over APIKey, which requests each page as it is reached.

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        if amount is not None:
            kwargs["amount"] = amount

        return _pages(list_api_keys.sync_detailed, kwargs)

    def list_page(
        self,
        *,
        amount: int | None = None,
        page: str | None = None,
    ) -> APIKeyPage:
        """List API keys: one page.

        Lists the authenticated account's API keys, oldest first, including revoked ones. The secret key
        itself is never returned again; `prefix` tells keys apart.

        Args:
            amount: Default: 50.
            page: The ``pagination.next_page_id`` of the previous page; the first page without it.

        Returns:
            APIKeyPage

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        if amount is not None:
            kwargs["amount"] = amount

        if page is not None:
            kwargs["page"] = page
        response = list_api_keys.sync_detailed(**kwargs)
        return cast(APIKeyPage, response.parsed)

    def create(
        self,
        *,
        name: str,
        permissions: builtins.list[
            Literal[
                "search",
                "read",
                "write",
                "create_index",
                "manage_index",
                "manage_members",
                "manage_organization",
            ]
        ],
        organization: str | None = None,
        indexes: builtins.list[str] | None = None,
        expires_at: datetime.datetime | None = None,
    ) -> APIKeyCreated:
        """Create an API key

        Creates a key that reaches one organization or all of the account's, a list of indexes or all of
        them, with a set of permissions, until it expires. A 404 means the organization or an index
        named does not exist or is not visible. Only a signed-in session can create, list or revoke
        keys. The response is the only time the secret key is shown, so store it securely. Send it as a
        bearer token: `Authorization: Bearer <key>`.

        Args:
            name: A name to tell the key apart, 1 to 128 characters.
            permissions: The permissions a key carries, each named once. Each one of ``"search"``,
                ``"read"``, ``"write"``, ``"create_index"``, ``"manage_index"``, ``"manage_members"``,
                ``"manage_organization"``.
            organization: An account or organization name. Accounts and organizations share one
                namespace. A name keeps the case it was created with, and any spelling that differs only in
                case refers to it; no other account or organization can take such a spelling.
            indexes: The indexes a key reaches, by name, in the key's one organization. Omitted for
                every index of its organizations, including indexes created later. A request names at least
                one; a key's list is empty once every index it named is deleted.
            expires_at: When the key stops working, at most one year ahead. Omitted for a key that never
                expires.

        Returns:
            APIKeyCreated

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        fields: dict[str, Any] = {}
        fields["name"] = name
        fields["permissions"] = [Permission(item) for item in permissions]
        if organization is not None:
            fields["organization"] = organization
        if indexes is not None:
            fields["indexes"] = indexes
        if expires_at is not None:
            fields["expires_at"] = expires_at
        kwargs["body"] = CreateAPIKeyRequest(**fields)

        response = create_api_key.sync_detailed(**kwargs)
        return cast(APIKeyCreated, response.parsed)

    def revoke(
        self,
        api_key_id: UUID,
    ) -> None:
        """Revoke an API key

        Revokes one of the authenticated account's API keys. Requests authenticated with it are refused
        from then on. A key that doesn't exist or belongs to another account is not found.

        Args:
            api_key_id:

        Returns:
            None

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        kwargs["api_key_id"] = api_key_id

        revoke_api_key.sync_detailed(**kwargs)


class Account:
    """User accounts: registration, sign-in and the current user."""

    def __init__(self, client: Client) -> None:
        self._client = client

    def register(
        self,
        *,
        name: str,
        email: str,
        password: str,
        invitation: str | None = None,
    ) -> User:
        """Register a local user

        A 409 has code `username_taken` when an account or an organization already holds the username,
        and code `email_taken` when an account already uses the email address. A 403 has code
        `invitation_required` when registration is by invitation and the request carries none, and code
        `invitation_invalid` when the invitation it carries was already used, was withdrawn or has
        expired. A valid invitation is accepted with the registration, and the account joins the
        organization it names, if any.

        Args:
            name: An account or organization name. Accounts and organizations share one namespace. A
                name keeps the case it was created with, and any spelling that differs only in case refers
                to it; no other account or organization can take such a spelling.
            email: The account's email address, at most 320 characters. No other account can use it.
            password: The password, 12 to 1,024 characters.
            invitation: The token of the invitation link the account was invited with. Required when
                registration is by invitation.

        Returns:
            User

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        fields: dict[str, Any] = {}
        fields["name"] = name
        fields["email"] = email
        fields["password"] = password
        if invitation is not None:
            fields["invitation"] = invitation
        kwargs["body"] = RegisterRequest(**fields)

        response = register_user.sync_detailed(**kwargs)
        return cast(User, response.parsed)

    def auth_options(
        self,
    ) -> AuthOptions:
        """Get the sign-in options

        How accounts are created on this service. The console reads it to decide whether to offer
        registration without an invitation.

        Returns:
            AuthOptions

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}

        response = get_auth_options.sync_detailed(**kwargs)
        return cast(AuthOptions, response.parsed)

    def check_invitation(
        self,
        *,
        token: str,
    ) -> InvitationPreview:
        """Check an invitation

        Reports what a pending invitation offers, so the registration form can show it. The token
        travels in the body, never in the URL. An invitation that was used, withdrawn or has expired is
        not found.

        Args:
            token: The token from the invitation link.

        Returns:
            InvitationPreview

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        fields: dict[str, Any] = {}
        fields["token"] = token
        kwargs["body"] = InvitationCheckRequest(**fields)

        response = check_invitation.sync_detailed(**kwargs)
        return cast(InvitationPreview, response.parsed)

    def username_availability(
        self,
        name: str,
    ) -> UsernameAvailability:
        """Check whether a username is available

        Reports whether an account can register this username now. Accounts and organizations share one
        namespace, so a name either one holds, in any case, is taken. The answer can change before the
        name is registered.

        Args:
            name: An account or organization name. Accounts and organizations share one namespace. A
                name keeps the case it was created with, and any spelling that differs only in case refers
                to it; no other account or organization can take such a spelling.

        Returns:
            UsernameAvailability

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        kwargs["name"] = name

        response = get_username_availability.sync_detailed(**kwargs)
        return cast(UsernameAvailability, response.parsed)

    def login(
        self,
        *,
        identifier: str,
        password: str,
    ) -> User:
        """Create a user session

        Signs in with a username or email address and a password, and starts a browser session: the
        response sets the session cookie and returns, in X-Csrf-Token, the token every state change made
        with that cookie must send. A 401 means the credentials were not accepted. Programs authenticate
        with an API key instead.

        Args:
            identifier: A username or an email address, matched case-insensitively.
            password: The account's password.

        Returns:
            User

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        fields: dict[str, Any] = {}
        fields["identifier"] = identifier
        fields["password"] = password
        kwargs["body"] = LoginRequest(**fields)

        response = login.sync_detailed(**kwargs)
        return cast(User, response.parsed)

    def logout(
        self,
    ) -> None:
        """Revoke the current session

        Ends the session that made the request and clears its cookie. Other sessions and API keys are
        unaffected.

        Returns:
            None

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}

        logout.sync_detailed(**kwargs)

    def me(
        self,
    ) -> User:
        """Get the current user

        Returns the account the request authenticates as, whether with a session or an API key. A
        session request also receives its CSRF token in X-Csrf-Token.

        Returns:
            User

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}

        response = get_current_user.sync_detailed(**kwargs)
        return cast(User, response.parsed)

    def change_password(
        self,
        *,
        current_password: str,
        new_password: str,
    ) -> None:
        """Change the current password

        Changes the signed-in account's password after checking the current one. Every other session of
        the account is signed out; the session that made the request stays signed in, and API keys keep
        working. A 401 means the current password was wrong.

        Args:
            current_password: The account's current password.
            new_password: The new password, 12 to 1,024 characters.

        Returns:
            None

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        fields: dict[str, Any] = {}
        fields["current_password"] = current_password
        fields["new_password"] = new_password
        kwargs["body"] = ChangePasswordRequest(**fields)

        change_password.sync_detailed(**kwargs)


class DeviceLogin:
    """Device login: obtain an API key by approving a code in the browser."""

    def __init__(self, client: Client) -> None:
        self._client = client

    def start(
        self,
        *,
        api_key_name: str,
        permissions: builtins.list[
            Literal[
                "search",
                "read",
                "write",
                "create_index",
                "manage_index",
                "manage_members",
                "manage_organization",
            ]
        ],
        organization: str | None = None,
        indexes: builtins.list[str] | None = None,
        expires_at: datetime.datetime | None = None,
    ) -> DeviceAuthorization:
        """Start device authorization

        Starts signing in a device, such as the command-line client, without entering a password on it.
        Show the user `user_code` and send them to `verification_uri` (or `verification_uri_complete`)
        to approve it in a signed-in browser, then poll for the API key with `device_code`. The
        authorization expires after `expires_in` seconds.

        Args:
            api_key_name: The name to give the API key the device receives, 1 to 128 characters.
            permissions: The permissions a key carries, each named once. Each one of ``"search"``,
                ``"read"``, ``"write"``, ``"create_index"``, ``"manage_index"``, ``"manage_members"``,
                ``"manage_organization"``.
            organization: An account or organization name. Accounts and organizations share one
                namespace. A name keeps the case it was created with, and any spelling that differs only in
                case refers to it; no other account or organization can take such a spelling.
            indexes: The indexes a key reaches, by name, in the key's one organization. Omitted for
                every index of its organizations, including indexes created later. A request names at least
                one; a key's list is empty once every index it named is deleted.
            expires_at: When the key stops working, at most one year ahead. Omitted for a key that never
                expires.

        Returns:
            DeviceAuthorization

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        fields: dict[str, Any] = {}
        fields["api_key_name"] = api_key_name
        fields["permissions"] = [Permission(item) for item in permissions]
        if organization is not None:
            fields["organization"] = organization
        if indexes is not None:
            fields["indexes"] = indexes
        if expires_at is not None:
            fields["expires_at"] = expires_at
        kwargs["body"] = DeviceAuthorizationRequest(**fields)

        response = start_device_authorization.sync_detailed(**kwargs)
        return cast(DeviceAuthorization, response.parsed)

    def approve(
        self,
        *,
        user_code: str,
        scope: KeyScope | None = None,
    ) -> None:
        """Approve device authorization

        Approves a pending device authorization, identified by the code the device shows. The device's
        next poll receives a new API key with the name it asked for. Without a scope it grants what the
        device asked for; a scope replaces that as a whole, narrower or wider. The key never does more
        than the approving account can. A code that is unknown, already decided or expired is not found.
        Only a signed-in session can approve.

        Args:
            user_code: The code the device shows. Hyphens, surrounding spaces and case are ignored.
            scope: What a key reaches and may do. A field left out sets no limit.

        Returns:
            None

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        fields: dict[str, Any] = {}
        fields["user_code"] = user_code
        if scope is not None:
            fields["scope"] = scope
        kwargs["body"] = DeviceApprovalRequest(**fields)

        approve_device_authorization.sync_detailed(**kwargs)

    def deny(
        self,
        *,
        user_code: str,
    ) -> None:
        """Deny device authorization

        Denies a pending device authorization, identified by the code the device shows. The device's
        next poll fails with code `access_denied`. A code that is unknown, already decided or expired is
        not found.

        Args:
            user_code: The code the device shows. Hyphens, surrounding spaces and case are ignored.

        Returns:
            None

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        fields: dict[str, Any] = {}
        fields["user_code"] = user_code
        kwargs["body"] = DeviceDecisionRequest(**fields)

        deny_device_authorization.sync_detailed(**kwargs)

    def poll(
        self,
        *,
        device_code: str,
    ) -> APIKeyCreated:
        """Poll for a device API key

        Exchanges an approved device code for an API key, once. Until the user decides, a poll fails
        with 400 and code `authorization_pending`: poll again after `interval` seconds. Polling sooner
        fails with `slow_down` and adds 5 seconds to the interval. A denied authorization fails with
        `access_denied`, and an unknown, expired or already used code with `expired_token`.

        Args:
            device_code: The `device_code` from starting the authorization.

        Returns:
            APIKeyCreated

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        fields: dict[str, Any] = {}
        fields["device_code"] = device_code
        kwargs["body"] = DeviceTokenRequest(**fields)

        response = poll_device_token.sync_detailed(**kwargs)
        return cast(APIKeyCreated, response.parsed)

    def get(
        self,
        *,
        user_code: str,
    ) -> PendingDeviceAuthorization:
        """Read a pending device authorization

        Returns the scope a pending device authorization asks for. Only a signed-in session can read
        one.

        Args:
            user_code: The code the device shows. Hyphens, surrounding spaces and case are ignored.

        Returns:
            PendingDeviceAuthorization

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        fields: dict[str, Any] = {}
        fields["user_code"] = user_code
        kwargs["body"] = DeviceDecisionRequest(**fields)

        response = get_device_authorization.sync_detailed(**kwargs)
        return cast(PendingDeviceAuthorization, response.parsed)


class Connections:
    """Apps the signed-in user connected through OAuth sign-in, such as MCP clients."""

    def __init__(self, client: Client) -> None:
        self._client = client

    def list(
        self,
    ) -> ConnectionPage:
        """List connections

        Lists the apps you have connected that are still in use: revoked and ended connections are left
        out. Newest first. Only a signed-in session can list them.

        Returns:
            ConnectionPage

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}

        response = list_connections.sync_detailed(**kwargs)
        return cast(ConnectionPage, response.parsed)

    def revoke(
        self,
        connection_id: UUID,
    ) -> None:
        """Revoke a connection

        Revokes one of the authenticated account's connections. The app's requests are refused from then
        on, and it must sign in again. A connection that doesn't exist, is already revoked or belongs to
        another account is not found. Only a signed-in session can revoke one.

        Args:
            connection_id:

        Returns:
            None

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        kwargs["connection_id"] = connection_id

        revoke_connection.sync_detailed(**kwargs)


class _GeneratedClient:
    """The API's resources."""

    organizations: Organizations
    indexes: Indexes
    documents: Documents
    search: Search
    api_keys: APIKeys
    account: Account
    device_login: DeviceLogin
    connections: Connections

    def __init__(self, client: Client) -> None:
        self._client = client
        self.organizations = Organizations(client)
        self.indexes = Indexes(client)
        self.documents = Documents(client)
        self.search = Search(client)
        self.api_keys = APIKeys(client)
        self.account = Account(client)
        self.device_login = DeviceLogin(client)
        self.connections = Connections(client)


class _IndexClient:
    """One index: its documents, search and settings. Make one with ``client.index("organization/index")``."""

    def __init__(self, client: Client, organization: str, index: str) -> None:
        self._client = client
        self._organization = organization
        self._index = index

    def search(
        self,
        *,
        pattern: str,
        mode: Literal["regex", "literal"] | None = None,
        case_sensitive: bool | None = None,
        whole_word: bool | None = None,
        multiline: bool | None = None,
        filter: str | None = None,
        lines_before: int | None = None,
        lines_after: int | None = None,
        amount: int | None = None,
    ) -> Iterator[QueryResult]:
        """Search an index: every result, page after page.

        Searches every searchable document in the index for a regular expression or literal text, and
        returns each match with the lines it covers, sorted by key, then line, then offset. A metadata
        filter restricts the search to matching documents, and context lines can be returned around each
        result. A pattern or filter that doesn't parse is rejected with 400 and code `invalid_pattern`
        or `invalid_filter`.

        Args:
            pattern: What to search for: an RE2 regular expression, or literal text when `mode` is
                `literal`. Required; at most 8,192 characters of valid UTF-8.
            mode: How to read the pattern: `regex` (the default) for RE2 syntax, without backreferences
                or lookaround, or `literal` to match its bytes exactly, with no escaping needed. One of
                ``"regex"``, ``"literal"``.
            case_sensitive: Whether case must match. Defaults to true. False matches under Unicode
                simple case folding; in a regex, `(?i)` does the same for part of the pattern.
            whole_word: Match only where the characters on either side of the match aren't word
                characters: letters, digits or `_`. Defaults to false. Valid only in literal mode.
            multiline: Let a match span lines. Without it a pattern matches within one line, `^` and `$`
                mark the line's edges, and a character class never matches a line break; a pattern that
                contains a line break is rejected. With it the pattern is matched against the whole
                document, `^` and `$` still mark line edges, `\\A` and `\\z` mark the document's edges, and
                a match may contain line breaks. Default: False.
            filter: Search only the documents whose metadata matches this expression, such as `path
                STARTSWITH 'src/' AND size < 1048576`. At most 8,192 characters. Omit it to search every
                document.
            lines_before: How many lines before each result to return with it, from the same document.
                Default: 0.
            lines_after: How many lines after each result to return with it, from the same document.
                Default: 0.
            amount: Default: 50.

        Returns:
            An iterator over QueryResult, which requests each page as it is reached.

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        kwargs["organization"] = self._organization
        kwargs["index"] = self._index
        if amount is not None:
            kwargs["amount"] = amount
        fields: dict[str, Any] = {}
        fields["pattern"] = pattern
        if mode is not None:
            fields["mode"] = QueryRequestMode(mode)
        if case_sensitive is not None:
            fields["case_sensitive"] = case_sensitive
        if whole_word is not None:
            fields["whole_word"] = whole_word
        if multiline is not None:
            fields["multiline"] = multiline
        if filter is not None:
            fields["filter_"] = filter
        if lines_before is not None:
            fields["lines_before"] = lines_before
        if lines_after is not None:
            fields["lines_after"] = lines_after
        kwargs["body"] = QueryRequest(**fields)

        return _pages(query_index.sync_detailed, kwargs)

    def search_page(
        self,
        *,
        pattern: str,
        mode: Literal["regex", "literal"] | None = None,
        case_sensitive: bool | None = None,
        whole_word: bool | None = None,
        multiline: bool | None = None,
        filter: str | None = None,
        lines_before: int | None = None,
        lines_after: int | None = None,
        amount: int | None = None,
        page: str | None = None,
    ) -> QueryPage:
        """Search an index: one page.

        Searches every searchable document in the index for a regular expression or literal text, and
        returns each match with the lines it covers, sorted by key, then line, then offset. A metadata
        filter restricts the search to matching documents, and context lines can be returned around each
        result. A pattern or filter that doesn't parse is rejected with 400 and code `invalid_pattern`
        or `invalid_filter`. Continue with `page` while `has_next` is true: a page can be empty while
        more results follow.

        Args:
            pattern: What to search for: an RE2 regular expression, or literal text when `mode` is
                `literal`. Required; at most 8,192 characters of valid UTF-8.
            mode: How to read the pattern: `regex` (the default) for RE2 syntax, without backreferences
                or lookaround, or `literal` to match its bytes exactly, with no escaping needed. One of
                ``"regex"``, ``"literal"``.
            case_sensitive: Whether case must match. Defaults to true. False matches under Unicode
                simple case folding; in a regex, `(?i)` does the same for part of the pattern.
            whole_word: Match only where the characters on either side of the match aren't word
                characters: letters, digits or `_`. Defaults to false. Valid only in literal mode.
            multiline: Let a match span lines. Without it a pattern matches within one line, `^` and `$`
                mark the line's edges, and a character class never matches a line break; a pattern that
                contains a line break is rejected. With it the pattern is matched against the whole
                document, `^` and `$` still mark line edges, `\\A` and `\\z` mark the document's edges, and
                a match may contain line breaks. Default: False.
            filter: Search only the documents whose metadata matches this expression, such as `path
                STARTSWITH 'src/' AND size < 1048576`. At most 8,192 characters. Omit it to search every
                document.
            lines_before: How many lines before each result to return with it, from the same document.
                Default: 0.
            lines_after: How many lines after each result to return with it, from the same document.
                Default: 0.
            amount: Default: 50.
            page: The ``pagination.next_page_id`` of the previous page; the first page without it.

        Returns:
            QueryPage

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        kwargs["organization"] = self._organization
        kwargs["index"] = self._index
        if amount is not None:
            kwargs["amount"] = amount
        fields: dict[str, Any] = {}
        fields["pattern"] = pattern
        if mode is not None:
            fields["mode"] = QueryRequestMode(mode)
        if case_sensitive is not None:
            fields["case_sensitive"] = case_sensitive
        if whole_word is not None:
            fields["whole_word"] = whole_word
        if multiline is not None:
            fields["multiline"] = multiline
        if filter is not None:
            fields["filter_"] = filter
        if lines_before is not None:
            fields["lines_before"] = lines_before
        if lines_after is not None:
            fields["lines_after"] = lines_after
        kwargs["body"] = QueryRequest(**fields)

        if page is not None:
            kwargs["page"] = page
        response = query_index.sync_detailed(**kwargs)
        return cast(QueryPage, response.parsed)

    def list_page(
        self,
        *,
        amount: int | None = None,
        prefix: str | None = None,
        delimiter: str | None = None,
        page: str | None = None,
    ) -> DocumentPage:
        """List documents: one page.

        Lists documents in key byte order, with each one's revision, size, metadata and whether a search
        can match it. Narrow the listing with `prefix`, and add `delimiter` to browse keys like a
        directory tree: keys that share the part up to the next delimiter are returned once, in
        `common_prefixes`.

        Args:
            amount: Default: 50.
            prefix:
            delimiter:
            page: The ``pagination.next_page_id`` of the previous page; the first page without it.

        Returns:
            DocumentPage

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        kwargs["organization"] = self._organization
        kwargs["index"] = self._index
        if amount is not None:
            kwargs["amount"] = amount
        if prefix is not None:
            kwargs["prefix"] = prefix
        if delimiter is not None:
            kwargs["delimiter"] = delimiter

        if page is not None:
            kwargs["page"] = page
        response = list_documents.sync_detailed(**kwargs)
        return cast(DocumentPage, response.parsed)

    def get(
        self,
        key: str,
        *,
        range: str | None = None,
    ) -> File:
        """Get a document

        Returns a document's content exactly as it was stored, its revision in the ETag header and its
        metadata in the X-Grepvine-Metadata header. Send a Range header to read one byte range; the
        response is then 206, or 416 when the range lies outside the document.

        Args:
            key:
            range:

        Returns:
            File

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        kwargs["organization"] = self._organization
        kwargs["index"] = self._index
        kwargs["key"] = key
        if range is not None:
            kwargs["range_"] = range

        response = get_document.sync_detailed(**kwargs)
        return cast(File, response.parsed)

    def _put(
        self,
        *,
        key: str,
        content: File,
        metadata: Metadata
        | Mapping[
            str,
            bool
            | int
            | str
            | TaggedBooleanMetadataValue
            | TaggedIntegerMetadataValue
            | TaggedNumberMetadataValue
            | TaggedStringMetadataValue
            | TaggedTimestampMetadataValue,
        ]
        | None = None,
        idempotency_key: str | None = None,
        if_match: str | None = None,
        if_none_match: Literal["*"] | None = None,
    ) -> MutationResult:
        """Store one document

        Stores one document of at most 1 GiB. Content that is valid UTF-8 and at most 100 MiB is
        searchable. Any other content, such as an image or a larger file, is stored, listed, and served
        by the document endpoints but is never matched by a search. The `searchable` field of a listing
        reports which applies.

        Args:
            key: The document's key: a UTF-8, POSIX-style path of at most 1,024 bytes, with no empty,
                `.` or `..` components. Storing a key that exists replaces that document.
            content: The document bytes, at most 1 GiB. Valid UTF-8 of at most 100 MiB is searchable;
                other content is stored without being searchable.
            metadata: Document metadata as a request sends it. Values are plain or tagged.
            idempotency_key:
            if_match:
            if_none_match: One of ``"*"``.

        Returns:
            MutationResult

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        kwargs["organization"] = self._organization
        kwargs["index"] = self._index
        if idempotency_key is not None:
            kwargs["idempotency_key"] = idempotency_key
        if if_match is not None:
            kwargs["if_match"] = if_match
        if if_none_match is not None:
            kwargs["if_none_match"] = PutDocumentIfNoneMatch(if_none_match)
        fields: dict[str, Any] = {}
        fields["key"] = key
        fields["content"] = content
        if metadata is not None:
            fields["metadata"] = _model(Metadata, metadata)
        kwargs["body"] = PutDocumentForm(**fields)

        response = put_document.sync_detailed(**kwargs)
        return cast(MutationResult, response.parsed)

    def delete(
        self,
        key: str,
        *,
        idempotency_key: str | None = None,
        if_match: str | None = None,
    ) -> MutationResult:
        """Delete one document

        Deletes one document. Send If-Match with a revision to delete it only if it still has that
        revision. Retrying with the same Idempotency-Key returns the original result. Once acknowledged,
        the document no longer matches any search.

        Args:
            key:
            idempotency_key:
            if_match:

        Returns:
            MutationResult

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        kwargs["organization"] = self._organization
        kwargs["index"] = self._index
        kwargs["key"] = key
        if idempotency_key is not None:
            kwargs["idempotency_key"] = idempotency_key
        if if_match is not None:
            kwargs["if_match"] = if_match

        response = delete_document.sync_detailed(**kwargs)
        return cast(MutationResult, response.parsed)

    def _put_batch(
        self,
        *,
        body: File,
        idempotency_key: str | None = None,
    ) -> MutationBatchResult:
        """Store a batch of documents

        Stores up to 2,048 documents. Each document is stored on its own: a document whose precondition
        fails is not stored, the others are, and the result of each document says which happened.
        Retrying
        with the same Idempotency-Key returns the same results and stores any document an interrupted
        attempt did not reach. Batch content is text carried as JSON strings, so every document stored
        this
        way is searchable. Store binary content, or a document over 16 MiB, with the
        single-document endpoint. The body may be sent with `Content-Encoding: gzip`; the service
        decodes it
        before applying the limits below, and answers any other content encoding with 415
        `unsupported_content_encoding`.

        Args:
            idempotency_key:

        Returns:
            MutationBatchResult

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        kwargs["organization"] = self._organization
        kwargs["index"] = self._index
        if idempotency_key is not None:
            kwargs["idempotency_key"] = idempotency_key
        kwargs["body"] = body

        response = put_objects.sync_detailed(**kwargs)
        return cast(MutationBatchResult, response.parsed)

    def delete_batch(
        self,
        *,
        objects: builtins.list[DeleteObjectRecord | Mapping[str, Any]],
        idempotency_key: str | None = None,
    ) -> MutationBatchResult:
        """Delete a batch of documents

        Deletes up to 2,048 documents. Each document is deleted on its own: a document that does not
        exist or whose precondition fails is not deleted, the others are, and the result of each
        document
        says which happened. Retrying with the same Idempotency-Key returns the same results.

        Args:
            objects: The documents to delete, 1 to 2,048.
            idempotency_key:

        Returns:
            MutationBatchResult

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        kwargs["organization"] = self._organization
        kwargs["index"] = self._index
        if idempotency_key is not None:
            kwargs["idempotency_key"] = idempotency_key
        fields: dict[str, Any] = {}
        fields["objects"] = [_model(DeleteObjectRecord, item) for item in objects]
        kwargs["body"] = DeleteObjectsRequest(**fields)

        response = delete_objects.sync_detailed(**kwargs)
        return cast(MutationBatchResult, response.parsed)

    def create(
        self,
        *,
        description: str | None = None,
        tags: IndexTags | Mapping[str, str] | None = None,
    ) -> IndexCreation:
        """Create an index

        Creates an empty index. Requires the owner or admin role. A new index is usually `ready` in the
        response; if it is still `creating`, read it until it is `ready`. A 409 means the organization
        already has an index with that name, in any case.

        Args:
            description: What the index holds, in Markdown. Empty when no description was set. Clients
                render it without raw HTML.
            tags: Key/value labels on the index, for example the commit it was synced from. At most 64
                tags. A key is 1 to 128 characters without whitespace or control characters; a value is at
                most 1,024 characters without control characters. Empty when none was set.

        Returns:
            IndexCreation: the answer as ``result``, and ``wait()`` to wait until the work is done.

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        kwargs["organization"] = self._organization
        fields: dict[str, Any] = {}
        fields["name"] = self._index
        if description is not None:
            fields["description"] = description
        if tags is not None:
            fields["tags"] = _model(IndexTags, tags)
        kwargs["body"] = CreateIndexRequest(**fields)

        response = create_index.sync_detailed(**kwargs)
        source = {**kwargs, **fields}
        polled = {
            "organization": source["organization"],
            "index": source["name"],
        }
        return IndexCreation(
            response.parsed,
            get_index.sync_detailed,
            {"client": self._client, **polled},
            "index " + "/".join(polled.values()),
        )

    def info(
        self,
    ) -> Index:
        """Get an index

        Returns one index with its current state, document count and size, and the progress of its
        background optimization while one runs. Any member can read it.

        Returns:
            Index

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        kwargs["organization"] = self._organization
        kwargs["index"] = self._index

        response = get_index.sync_detailed(**kwargs)
        return cast(Index, response.parsed)

    def update(
        self,
        *,
        description: str | None = None,
        tags: IndexTagChanges | Mapping[str, None | str] | None = None,
    ) -> Index:
        """Update an index

        Changes the index's description or tags. A field absent from the request is left as it is. The
        name is immutable.

        Args:
            description: What the index holds, in Markdown. Empty when no description was set. Clients
                render it without raw HTML.
            tags: Tags to set, by key, and tags to remove, given as null. A key absent from the map is
                unchanged.

        Returns:
            Index

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        kwargs["organization"] = self._organization
        kwargs["index"] = self._index
        fields: dict[str, Any] = {}
        if description is not None:
            fields["description"] = description
        if tags is not None:
            fields["tags"] = _model(IndexTagChanges, tags)
        kwargs["body"] = UpdateIndexRequest(**fields)

        response = update_index.sync_detailed(**kwargs)
        return cast(Index, response.parsed)

    def delete_index(
        self,
    ) -> IndexDeletion:
        """Delete an index

        Starts deleting an index and all its documents. Requires the owner or admin role. The index is
        `deleting` until the deletion finishes in the background, and it can't be undone.

        Returns:
            IndexDeletion: the answer as ``result``, and ``wait()`` to wait until the work is done.

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        kwargs["organization"] = self._organization
        kwargs["index"] = self._index

        response = delete_index.sync_detailed(**kwargs)
        source = kwargs
        polled = {
            "organization": source["organization"],
            "index": source["index"],
        }
        return IndexDeletion(
            response.parsed,
            get_index.sync_detailed,
            {"client": self._client, **polled},
            "index " + "/".join(polled.values()),
        )


class AsyncMembers:
    """The members of an organization and their roles."""

    def __init__(self, client: Client) -> None:
        self._client = client

    def list(
        self,
        organization: str,
        *,
        amount: int | None = None,
    ) -> AsyncIterator[Member]:
        """List organization members: every result, page after page.

        Lists an organization's members and their roles, ordered by name. Requires the owner or admin
        role.

        Args:
            organization: An account or organization name. Accounts and organizations share one
                namespace. A name keeps the case it was created with, and any spelling that differs only in
                case refers to it; no other account or organization can take such a spelling.
            amount: Default: 50.

        Returns:
            An async iterator over Member, which requests each page as it is reached.

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        kwargs["organization"] = organization
        if amount is not None:
            kwargs["amount"] = amount

        return _async_pages(list_organization_members.asyncio_detailed, kwargs)

    async def list_page(
        self,
        organization: str,
        *,
        amount: int | None = None,
        page: str | None = None,
    ) -> MemberPage:
        """List organization members: one page.

        Lists an organization's members and their roles, ordered by name. Requires the owner or admin
        role.

        Args:
            organization: An account or organization name. Accounts and organizations share one
                namespace. A name keeps the case it was created with, and any spelling that differs only in
                case refers to it; no other account or organization can take such a spelling.
            amount: Default: 50.
            page: The ``pagination.next_page_id`` of the previous page; the first page without it.

        Returns:
            MemberPage

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        kwargs["organization"] = organization
        if amount is not None:
            kwargs["amount"] = amount

        if page is not None:
            kwargs["page"] = page
        response = await list_organization_members.asyncio_detailed(**kwargs)
        return cast(MemberPage, response.parsed)

    async def add(
        self,
        organization: str,
        *,
        user: str,
        role: Literal["admin", "developer", "reader"],
    ) -> Member:
        """Add an organization member

        Adds an existing account to the organization with the admin, developer or reader role. Requires
        the owner or admin role. An organization has one owner, changed only by transferring ownership.

        Args:
            organization: An account or organization name. Accounts and organizations share one
                namespace. A name keeps the case it was created with, and any spelling that differs only in
                case refers to it; no other account or organization can take such a spelling.
            user: An account or organization name. Accounts and organizations share one namespace. A
                name keeps the case it was created with, and any spelling that differs only in case refers
                to it; no other account or organization can take such a spelling.
            role: The role to grant. `owner` is granted only by transferring ownership. One of
                ``"admin"``, ``"developer"``, ``"reader"``.

        Returns:
            Member

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        kwargs["organization"] = organization
        fields: dict[str, Any] = {}
        fields["user"] = user
        fields["role"] = AddMemberRequestRole(role)
        kwargs["body"] = AddMemberRequest(**fields)

        response = await add_organization_member.asyncio_detailed(**kwargs)
        return cast(Member, response.parsed)

    async def update(
        self,
        organization: str,
        user: str,
        *,
        role: Literal["admin", "developer", "reader"],
    ) -> Member:
        """Change an organization member role

        Changes a member's role to admin, developer or reader. Requires the owner or admin role. The
        owner's role changes only by transferring ownership.

        Args:
            organization: An account or organization name. Accounts and organizations share one
                namespace. A name keeps the case it was created with, and any spelling that differs only in
                case refers to it; no other account or organization can take such a spelling.
            user: An account or organization name. Accounts and organizations share one namespace. A
                name keeps the case it was created with, and any spelling that differs only in case refers
                to it; no other account or organization can take such a spelling.
            role: The new role. `owner` is granted only by transferring ownership. One of ``"admin"``,
                ``"developer"``, ``"reader"``.

        Returns:
            Member

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        kwargs["organization"] = organization
        kwargs["user"] = user
        fields: dict[str, Any] = {}
        fields["role"] = UpdateMemberRequestRole(role)
        kwargs["body"] = UpdateMemberRequest(**fields)

        response = await update_organization_member.asyncio_detailed(**kwargs)
        return cast(Member, response.parsed)

    async def remove(
        self,
        organization: str,
        user: str,
    ) -> None:
        """Remove an organization member

        Removes a member from the organization. Requires the owner or admin role. The owner can't be
        removed; transfer ownership first.

        Args:
            organization: An account or organization name. Accounts and organizations share one
                namespace. A name keeps the case it was created with, and any spelling that differs only in
                case refers to it; no other account or organization can take such a spelling.
            user: An account or organization name. Accounts and organizations share one namespace. A
                name keeps the case it was created with, and any spelling that differs only in case refers
                to it; no other account or organization can take such a spelling.

        Returns:
            None

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        kwargs["organization"] = organization
        kwargs["user"] = user

        await remove_organization_member.asyncio_detailed(**kwargs)


class AsyncOrganizations:
    """Organizations: create, read, delete and transfer them."""

    members: AsyncMembers

    def __init__(self, client: Client) -> None:
        self._client = client
        self.members = AsyncMembers(client)

    def list(
        self,
        *,
        amount: int | None = None,
    ) -> AsyncIterator[Organization]:
        """List organizations: every result, page after page.

        Lists the organizations the authenticated account belongs to, with its role in each, ordered by
        name.

        Args:
            amount: Default: 50.

        Returns:
            An async iterator over Organization, which requests each page as it is reached.

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        if amount is not None:
            kwargs["amount"] = amount

        return _async_pages(list_organizations.asyncio_detailed, kwargs)

    async def list_page(
        self,
        *,
        amount: int | None = None,
        page: str | None = None,
    ) -> OrganizationPage:
        """List organizations: one page.

        Lists the organizations the authenticated account belongs to, with its role in each, ordered by
        name.

        Args:
            amount: Default: 50.
            page: The ``pagination.next_page_id`` of the previous page; the first page without it.

        Returns:
            OrganizationPage

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        if amount is not None:
            kwargs["amount"] = amount

        if page is not None:
            kwargs["page"] = page
        response = await list_organizations.asyncio_detailed(**kwargs)
        return cast(OrganizationPage, response.parsed)

    async def create(
        self,
        *,
        name: str,
    ) -> Organization:
        """Create an organization

        Creates an organization owned by the authenticated account. Accounts and organizations share one
        namespace, so a 409 means an account or organization already holds the name, in any case.

        Args:
            name: An account or organization name. Accounts and organizations share one namespace. A
                name keeps the case it was created with, and any spelling that differs only in case refers
                to it; no other account or organization can take such a spelling.

        Returns:
            Organization

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        fields: dict[str, Any] = {}
        fields["name"] = name
        kwargs["body"] = CreateOrganizationRequest(**fields)

        response = await create_organization.asyncio_detailed(**kwargs)
        return cast(Organization, response.parsed)

    async def get(
        self,
        organization: str,
    ) -> Organization:
        """Get an organization

        Returns an organization the authenticated account belongs to, with its role there. It answers
        for a suspended organization too, and reports `suspended`.

        Args:
            organization: An account or organization name. Accounts and organizations share one
                namespace. A name keeps the case it was created with, and any spelling that differs only in
                case refers to it; no other account or organization can take such a spelling.

        Returns:
            Organization

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        kwargs["organization"] = organization

        response = await get_organization.asyncio_detailed(**kwargs)
        return cast(Organization, response.parsed)

    async def delete(
        self,
        organization: str,
    ) -> None:
        """Delete an organization

        Starts deleting an organization with all its indexes and documents. Only the owner can delete
        it. The deletion finishes in the background and can't be undone.

        Args:
            organization: An account or organization name. Accounts and organizations share one
                namespace. A name keeps the case it was created with, and any spelling that differs only in
                case refers to it; no other account or organization can take such a spelling.

        Returns:
            None

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        kwargs["organization"] = organization

        await delete_organization.asyncio_detailed(**kwargs)

    async def transfer_ownership(
        self,
        organization: str,
        *,
        user: str,
    ) -> None:
        """Transfer organization ownership

        Makes another member the owner. Only the owner can transfer ownership, and the previous owner
        stays a member with the admin role. The new owner must already be a member, and not one with
        time-limited access.

        Args:
            organization: An account or organization name. Accounts and organizations share one
                namespace. A name keeps the case it was created with, and any spelling that differs only in
                case refers to it; no other account or organization can take such a spelling.
            user: An account or organization name. Accounts and organizations share one namespace. A
                name keeps the case it was created with, and any spelling that differs only in case refers
                to it; no other account or organization can take such a spelling.

        Returns:
            None

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        kwargs["organization"] = organization
        fields: dict[str, Any] = {}
        fields["user"] = user
        kwargs["body"] = TransferOwnershipRequest(**fields)

        await transfer_organization_ownership.asyncio_detailed(**kwargs)


class AsyncIndexes:
    """Indexes in an organization."""

    def __init__(self, client: Client) -> None:
        self._client = client

    def list(
        self,
        organization: str,
        *,
        amount: int | None = None,
        prefix: str | None = None,
    ) -> AsyncIterator[IndexSummary]:
        """List indexes: every result, page after page.

        Lists the organization's indexes, ordered by name. Any member can list them.

        Args:
            organization: An account or organization name. Accounts and organizations share one
                namespace. A name keeps the case it was created with, and any spelling that differs only in
                case refers to it; no other account or organization can take such a spelling.
            amount: Default: 50.
            prefix:

        Returns:
            An async iterator over IndexSummary, which requests each page as it is reached.

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        kwargs["organization"] = organization
        if amount is not None:
            kwargs["amount"] = amount
        if prefix is not None:
            kwargs["prefix"] = prefix

        return _async_pages(list_indexes.asyncio_detailed, kwargs)

    async def list_page(
        self,
        organization: str,
        *,
        amount: int | None = None,
        prefix: str | None = None,
        page: str | None = None,
    ) -> IndexPage:
        """List indexes: one page.

        Lists the organization's indexes, ordered by name. Any member can list them.

        Args:
            organization: An account or organization name. Accounts and organizations share one
                namespace. A name keeps the case it was created with, and any spelling that differs only in
                case refers to it; no other account or organization can take such a spelling.
            amount: Default: 50.
            prefix:
            page: The ``pagination.next_page_id`` of the previous page; the first page without it.

        Returns:
            IndexPage

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        kwargs["organization"] = organization
        if amount is not None:
            kwargs["amount"] = amount
        if prefix is not None:
            kwargs["prefix"] = prefix

        if page is not None:
            kwargs["page"] = page
        response = await list_indexes.asyncio_detailed(**kwargs)
        return cast(IndexPage, response.parsed)

    async def create(
        self,
        organization: str,
        *,
        name: str,
        description: str | None = None,
        tags: IndexTags | Mapping[str, str] | None = None,
    ) -> AsyncIndexCreation:
        """Create an index

        Creates an empty index. Requires the owner or admin role. A new index is usually `ready` in the
        response; if it is still `creating`, read it until it is `ready`. A 409 means the organization
        already has an index with that name, in any case.

        Args:
            organization: An account or organization name. Accounts and organizations share one
                namespace. A name keeps the case it was created with, and any spelling that differs only in
                case refers to it; no other account or organization can take such a spelling.
            name: An index name, unique in its organization. A name keeps the case it was created with,
                and any spelling that differs only in case refers to it; no other index in the organization
                can take such a spelling.
            description: What the index holds, in Markdown. Empty when no description was set. Clients
                render it without raw HTML.
            tags: Key/value labels on the index, for example the commit it was synced from. At most 64
                tags. A key is 1 to 128 characters without whitespace or control characters; a value is at
                most 1,024 characters without control characters. Empty when none was set.

        Returns:
            AsyncIndexCreation: the answer as ``result``, and ``wait()`` to wait until the work is done.

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        kwargs["organization"] = organization
        fields: dict[str, Any] = {}
        fields["name"] = name
        if description is not None:
            fields["description"] = description
        if tags is not None:
            fields["tags"] = _model(IndexTags, tags)
        kwargs["body"] = CreateIndexRequest(**fields)

        response = await create_index.asyncio_detailed(**kwargs)
        source = {**kwargs, **fields}
        polled = {
            "organization": source["organization"],
            "index": source["name"],
        }
        return AsyncIndexCreation(
            response.parsed,
            get_index.asyncio_detailed,
            {"client": self._client, **polled},
            "index " + "/".join(polled.values()),
        )

    async def get(
        self,
        organization: str,
        index: str,
    ) -> Index:
        """Get an index

        Returns one index with its current state, document count and size, and the progress of its
        background optimization while one runs. Any member can read it.

        Args:
            organization: An account or organization name. Accounts and organizations share one
                namespace. A name keeps the case it was created with, and any spelling that differs only in
                case refers to it; no other account or organization can take such a spelling.
            index: An index name, unique in its organization. A name keeps the case it was created with,
                and any spelling that differs only in case refers to it; no other index in the organization
                can take such a spelling.

        Returns:
            Index

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        kwargs["organization"] = organization
        kwargs["index"] = index

        response = await get_index.asyncio_detailed(**kwargs)
        return cast(Index, response.parsed)

    async def update(
        self,
        organization: str,
        index: str,
        *,
        description: str | None = None,
        tags: IndexTagChanges | Mapping[str, None | str] | None = None,
    ) -> Index:
        """Update an index

        Changes the index's description or tags. A field absent from the request is left as it is. The
        name is immutable.

        Args:
            organization: An account or organization name. Accounts and organizations share one
                namespace. A name keeps the case it was created with, and any spelling that differs only in
                case refers to it; no other account or organization can take such a spelling.
            index: An index name, unique in its organization. A name keeps the case it was created with,
                and any spelling that differs only in case refers to it; no other index in the organization
                can take such a spelling.
            description: What the index holds, in Markdown. Empty when no description was set. Clients
                render it without raw HTML.
            tags: Tags to set, by key, and tags to remove, given as null. A key absent from the map is
                unchanged.

        Returns:
            Index

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        kwargs["organization"] = organization
        kwargs["index"] = index
        fields: dict[str, Any] = {}
        if description is not None:
            fields["description"] = description
        if tags is not None:
            fields["tags"] = _model(IndexTagChanges, tags)
        kwargs["body"] = UpdateIndexRequest(**fields)

        response = await update_index.asyncio_detailed(**kwargs)
        return cast(Index, response.parsed)

    async def delete(
        self,
        organization: str,
        index: str,
    ) -> AsyncIndexDeletion:
        """Delete an index

        Starts deleting an index and all its documents. Requires the owner or admin role. The index is
        `deleting` until the deletion finishes in the background, and it can't be undone.

        Args:
            organization: An account or organization name. Accounts and organizations share one
                namespace. A name keeps the case it was created with, and any spelling that differs only in
                case refers to it; no other account or organization can take such a spelling.
            index: An index name, unique in its organization. A name keeps the case it was created with,
                and any spelling that differs only in case refers to it; no other index in the organization
                can take such a spelling.

        Returns:
            AsyncIndexDeletion: the answer as ``result``, and ``wait()`` to wait until the work is done.

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        kwargs["organization"] = organization
        kwargs["index"] = index

        response = await delete_index.asyncio_detailed(**kwargs)
        source = kwargs
        polled = {
            "organization": source["organization"],
            "index": source["index"],
        }
        return AsyncIndexDeletion(
            response.parsed,
            get_index.asyncio_detailed,
            {"client": self._client, **polled},
            "index " + "/".join(polled.values()),
        )


class AsyncDocuments:
    """The documents of an index."""

    def __init__(self, client: Client) -> None:
        self._client = client

    async def list_page(
        self,
        organization: str,
        index: str,
        *,
        amount: int | None = None,
        prefix: str | None = None,
        delimiter: str | None = None,
        page: str | None = None,
    ) -> DocumentPage:
        """List documents: one page.

        Lists documents in key byte order, with each one's revision, size, metadata and whether a search
        can match it. Narrow the listing with `prefix`, and add `delimiter` to browse keys like a
        directory tree: keys that share the part up to the next delimiter are returned once, in
        `common_prefixes`.

        Args:
            organization: An account or organization name. Accounts and organizations share one
                namespace. A name keeps the case it was created with, and any spelling that differs only in
                case refers to it; no other account or organization can take such a spelling.
            index: An index name, unique in its organization. A name keeps the case it was created with,
                and any spelling that differs only in case refers to it; no other index in the organization
                can take such a spelling.
            amount: Default: 50.
            prefix:
            delimiter:
            page: The ``pagination.next_page_id`` of the previous page; the first page without it.

        Returns:
            DocumentPage

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        kwargs["organization"] = organization
        kwargs["index"] = index
        if amount is not None:
            kwargs["amount"] = amount
        if prefix is not None:
            kwargs["prefix"] = prefix
        if delimiter is not None:
            kwargs["delimiter"] = delimiter

        if page is not None:
            kwargs["page"] = page
        response = await list_documents.asyncio_detailed(**kwargs)
        return cast(DocumentPage, response.parsed)

    async def put(
        self,
        organization: str,
        index: str,
        *,
        key: str,
        content: File,
        metadata: Metadata
        | Mapping[
            str,
            bool
            | int
            | str
            | TaggedBooleanMetadataValue
            | TaggedIntegerMetadataValue
            | TaggedNumberMetadataValue
            | TaggedStringMetadataValue
            | TaggedTimestampMetadataValue,
        ]
        | None = None,
        idempotency_key: str | None = None,
        if_match: str | None = None,
        if_none_match: Literal["*"] | None = None,
    ) -> MutationResult:
        """Store one document

        Stores one document of at most 1 GiB. Content that is valid UTF-8 and at most 100 MiB is
        searchable. Any other content, such as an image or a larger file, is stored, listed, and served
        by the document endpoints but is never matched by a search. The `searchable` field of a listing
        reports which applies.

        Args:
            organization: An account or organization name. Accounts and organizations share one
                namespace. A name keeps the case it was created with, and any spelling that differs only in
                case refers to it; no other account or organization can take such a spelling.
            index: An index name, unique in its organization. A name keeps the case it was created with,
                and any spelling that differs only in case refers to it; no other index in the organization
                can take such a spelling.
            key: The document's key: a UTF-8, POSIX-style path of at most 1,024 bytes, with no empty,
                `.` or `..` components. Storing a key that exists replaces that document.
            content: The document bytes, at most 1 GiB. Valid UTF-8 of at most 100 MiB is searchable;
                other content is stored without being searchable.
            metadata: Document metadata as a request sends it. Values are plain or tagged.
            idempotency_key:
            if_match:
            if_none_match: One of ``"*"``.

        Returns:
            MutationResult

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        kwargs["organization"] = organization
        kwargs["index"] = index
        if idempotency_key is not None:
            kwargs["idempotency_key"] = idempotency_key
        if if_match is not None:
            kwargs["if_match"] = if_match
        if if_none_match is not None:
            kwargs["if_none_match"] = PutDocumentIfNoneMatch(if_none_match)
        fields: dict[str, Any] = {}
        fields["key"] = key
        fields["content"] = content
        if metadata is not None:
            fields["metadata"] = _model(Metadata, metadata)
        kwargs["body"] = PutDocumentForm(**fields)

        response = await put_document.asyncio_detailed(**kwargs)
        return cast(MutationResult, response.parsed)

    async def get(
        self,
        organization: str,
        index: str,
        key: str,
        *,
        range: str | None = None,
    ) -> File:
        """Get a document

        Returns a document's content exactly as it was stored, its revision in the ETag header and its
        metadata in the X-Grepvine-Metadata header. Send a Range header to read one byte range; the
        response is then 206, or 416 when the range lies outside the document.

        Args:
            organization: An account or organization name. Accounts and organizations share one
                namespace. A name keeps the case it was created with, and any spelling that differs only in
                case refers to it; no other account or organization can take such a spelling.
            index: An index name, unique in its organization. A name keeps the case it was created with,
                and any spelling that differs only in case refers to it; no other index in the organization
                can take such a spelling.
            key:
            range:

        Returns:
            File

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        kwargs["organization"] = organization
        kwargs["index"] = index
        kwargs["key"] = key
        if range is not None:
            kwargs["range_"] = range

        response = await get_document.asyncio_detailed(**kwargs)
        return cast(File, response.parsed)

    async def delete(
        self,
        organization: str,
        index: str,
        key: str,
        *,
        idempotency_key: str | None = None,
        if_match: str | None = None,
    ) -> MutationResult:
        """Delete one document

        Deletes one document. Send If-Match with a revision to delete it only if it still has that
        revision. Retrying with the same Idempotency-Key returns the original result. Once acknowledged,
        the document no longer matches any search.

        Args:
            organization: An account or organization name. Accounts and organizations share one
                namespace. A name keeps the case it was created with, and any spelling that differs only in
                case refers to it; no other account or organization can take such a spelling.
            index: An index name, unique in its organization. A name keeps the case it was created with,
                and any spelling that differs only in case refers to it; no other index in the organization
                can take such a spelling.
            key:
            idempotency_key:
            if_match:

        Returns:
            MutationResult

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        kwargs["organization"] = organization
        kwargs["index"] = index
        kwargs["key"] = key
        if idempotency_key is not None:
            kwargs["idempotency_key"] = idempotency_key
        if if_match is not None:
            kwargs["if_match"] = if_match

        response = await delete_document.asyncio_detailed(**kwargs)
        return cast(MutationResult, response.parsed)

    async def put_batch(
        self,
        organization: str,
        index: str,
        *,
        body: File,
        idempotency_key: str | None = None,
    ) -> MutationBatchResult:
        """Store a batch of documents

        Stores up to 2,048 documents. Each document is stored on its own: a document whose precondition
        fails is not stored, the others are, and the result of each document says which happened.
        Retrying
        with the same Idempotency-Key returns the same results and stores any document an interrupted
        attempt did not reach. Batch content is text carried as JSON strings, so every document stored
        this
        way is searchable. Store binary content, or a document over 16 MiB, with the
        single-document endpoint. The body may be sent with `Content-Encoding: gzip`; the service
        decodes it
        before applying the limits below, and answers any other content encoding with 415
        `unsupported_content_encoding`.

        Args:
            organization: An account or organization name. Accounts and organizations share one
                namespace. A name keeps the case it was created with, and any spelling that differs only in
                case refers to it; no other account or organization can take such a spelling.
            index: An index name, unique in its organization. A name keeps the case it was created with,
                and any spelling that differs only in case refers to it; no other index in the organization
                can take such a spelling.
            idempotency_key:

        Returns:
            MutationBatchResult

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        kwargs["organization"] = organization
        kwargs["index"] = index
        if idempotency_key is not None:
            kwargs["idempotency_key"] = idempotency_key
        kwargs["body"] = body

        response = await put_objects.asyncio_detailed(**kwargs)
        return cast(MutationBatchResult, response.parsed)

    async def delete_batch(
        self,
        organization: str,
        index: str,
        *,
        objects: builtins.list[DeleteObjectRecord | Mapping[str, Any]],
        idempotency_key: str | None = None,
    ) -> MutationBatchResult:
        """Delete a batch of documents

        Deletes up to 2,048 documents. Each document is deleted on its own: a document that does not
        exist or whose precondition fails is not deleted, the others are, and the result of each
        document
        says which happened. Retrying with the same Idempotency-Key returns the same results.

        Args:
            organization: An account or organization name. Accounts and organizations share one
                namespace. A name keeps the case it was created with, and any spelling that differs only in
                case refers to it; no other account or organization can take such a spelling.
            index: An index name, unique in its organization. A name keeps the case it was created with,
                and any spelling that differs only in case refers to it; no other index in the organization
                can take such a spelling.
            objects: The documents to delete, 1 to 2,048.
            idempotency_key:

        Returns:
            MutationBatchResult

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        kwargs["organization"] = organization
        kwargs["index"] = index
        if idempotency_key is not None:
            kwargs["idempotency_key"] = idempotency_key
        fields: dict[str, Any] = {}
        fields["objects"] = [_model(DeleteObjectRecord, item) for item in objects]
        kwargs["body"] = DeleteObjectsRequest(**fields)

        response = await delete_objects.asyncio_detailed(**kwargs)
        return cast(MutationBatchResult, response.parsed)


class AsyncSearch:
    """Search over the documents of an index."""

    def __init__(self, client: Client) -> None:
        self._client = client

    def query(
        self,
        organization: str,
        index: str,
        *,
        pattern: str,
        mode: Literal["regex", "literal"] | None = None,
        case_sensitive: bool | None = None,
        whole_word: bool | None = None,
        multiline: bool | None = None,
        filter: str | None = None,
        lines_before: int | None = None,
        lines_after: int | None = None,
        amount: int | None = None,
    ) -> AsyncIterator[QueryResult]:
        """Search an index: every result, page after page.

        Searches every searchable document in the index for a regular expression or literal text, and
        returns each match with the lines it covers, sorted by key, then line, then offset. A metadata
        filter restricts the search to matching documents, and context lines can be returned around each
        result. A pattern or filter that doesn't parse is rejected with 400 and code `invalid_pattern`
        or `invalid_filter`.

        Args:
            organization: An account or organization name. Accounts and organizations share one
                namespace. A name keeps the case it was created with, and any spelling that differs only in
                case refers to it; no other account or organization can take such a spelling.
            index: An index name, unique in its organization. A name keeps the case it was created with,
                and any spelling that differs only in case refers to it; no other index in the organization
                can take such a spelling.
            pattern: What to search for: an RE2 regular expression, or literal text when `mode` is
                `literal`. Required; at most 8,192 characters of valid UTF-8.
            mode: How to read the pattern: `regex` (the default) for RE2 syntax, without backreferences
                or lookaround, or `literal` to match its bytes exactly, with no escaping needed. One of
                ``"regex"``, ``"literal"``.
            case_sensitive: Whether case must match. Defaults to true. False matches under Unicode
                simple case folding; in a regex, `(?i)` does the same for part of the pattern.
            whole_word: Match only where the characters on either side of the match aren't word
                characters: letters, digits or `_`. Defaults to false. Valid only in literal mode.
            multiline: Let a match span lines. Without it a pattern matches within one line, `^` and `$`
                mark the line's edges, and a character class never matches a line break; a pattern that
                contains a line break is rejected. With it the pattern is matched against the whole
                document, `^` and `$` still mark line edges, `\\A` and `\\z` mark the document's edges, and
                a match may contain line breaks. Default: False.
            filter: Search only the documents whose metadata matches this expression, such as `path
                STARTSWITH 'src/' AND size < 1048576`. At most 8,192 characters. Omit it to search every
                document.
            lines_before: How many lines before each result to return with it, from the same document.
                Default: 0.
            lines_after: How many lines after each result to return with it, from the same document.
                Default: 0.
            amount: Default: 50.

        Returns:
            An async iterator over QueryResult, which requests each page as it is reached.

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        kwargs["organization"] = organization
        kwargs["index"] = index
        if amount is not None:
            kwargs["amount"] = amount
        fields: dict[str, Any] = {}
        fields["pattern"] = pattern
        if mode is not None:
            fields["mode"] = QueryRequestMode(mode)
        if case_sensitive is not None:
            fields["case_sensitive"] = case_sensitive
        if whole_word is not None:
            fields["whole_word"] = whole_word
        if multiline is not None:
            fields["multiline"] = multiline
        if filter is not None:
            fields["filter_"] = filter
        if lines_before is not None:
            fields["lines_before"] = lines_before
        if lines_after is not None:
            fields["lines_after"] = lines_after
        kwargs["body"] = QueryRequest(**fields)

        return _async_pages(query_index.asyncio_detailed, kwargs)

    async def query_page(
        self,
        organization: str,
        index: str,
        *,
        pattern: str,
        mode: Literal["regex", "literal"] | None = None,
        case_sensitive: bool | None = None,
        whole_word: bool | None = None,
        multiline: bool | None = None,
        filter: str | None = None,
        lines_before: int | None = None,
        lines_after: int | None = None,
        amount: int | None = None,
        page: str | None = None,
    ) -> QueryPage:
        """Search an index: one page.

        Searches every searchable document in the index for a regular expression or literal text, and
        returns each match with the lines it covers, sorted by key, then line, then offset. A metadata
        filter restricts the search to matching documents, and context lines can be returned around each
        result. A pattern or filter that doesn't parse is rejected with 400 and code `invalid_pattern`
        or `invalid_filter`. Continue with `page` while `has_next` is true: a page can be empty while
        more results follow.

        Args:
            organization: An account or organization name. Accounts and organizations share one
                namespace. A name keeps the case it was created with, and any spelling that differs only in
                case refers to it; no other account or organization can take such a spelling.
            index: An index name, unique in its organization. A name keeps the case it was created with,
                and any spelling that differs only in case refers to it; no other index in the organization
                can take such a spelling.
            pattern: What to search for: an RE2 regular expression, or literal text when `mode` is
                `literal`. Required; at most 8,192 characters of valid UTF-8.
            mode: How to read the pattern: `regex` (the default) for RE2 syntax, without backreferences
                or lookaround, or `literal` to match its bytes exactly, with no escaping needed. One of
                ``"regex"``, ``"literal"``.
            case_sensitive: Whether case must match. Defaults to true. False matches under Unicode
                simple case folding; in a regex, `(?i)` does the same for part of the pattern.
            whole_word: Match only where the characters on either side of the match aren't word
                characters: letters, digits or `_`. Defaults to false. Valid only in literal mode.
            multiline: Let a match span lines. Without it a pattern matches within one line, `^` and `$`
                mark the line's edges, and a character class never matches a line break; a pattern that
                contains a line break is rejected. With it the pattern is matched against the whole
                document, `^` and `$` still mark line edges, `\\A` and `\\z` mark the document's edges, and
                a match may contain line breaks. Default: False.
            filter: Search only the documents whose metadata matches this expression, such as `path
                STARTSWITH 'src/' AND size < 1048576`. At most 8,192 characters. Omit it to search every
                document.
            lines_before: How many lines before each result to return with it, from the same document.
                Default: 0.
            lines_after: How many lines after each result to return with it, from the same document.
                Default: 0.
            amount: Default: 50.
            page: The ``pagination.next_page_id`` of the previous page; the first page without it.

        Returns:
            QueryPage

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        kwargs["organization"] = organization
        kwargs["index"] = index
        if amount is not None:
            kwargs["amount"] = amount
        fields: dict[str, Any] = {}
        fields["pattern"] = pattern
        if mode is not None:
            fields["mode"] = QueryRequestMode(mode)
        if case_sensitive is not None:
            fields["case_sensitive"] = case_sensitive
        if whole_word is not None:
            fields["whole_word"] = whole_word
        if multiline is not None:
            fields["multiline"] = multiline
        if filter is not None:
            fields["filter_"] = filter
        if lines_before is not None:
            fields["lines_before"] = lines_before
        if lines_after is not None:
            fields["lines_after"] = lines_after
        kwargs["body"] = QueryRequest(**fields)

        if page is not None:
            kwargs["page"] = page
        response = await query_index.asyncio_detailed(**kwargs)
        return cast(QueryPage, response.parsed)


class AsyncAPIKeys:
    """The API keys of the signed-in user."""

    def __init__(self, client: Client) -> None:
        self._client = client

    def list(
        self,
        *,
        amount: int | None = None,
    ) -> AsyncIterator[APIKey]:
        """List API keys: every result, page after page.

        Lists the authenticated account's API keys, oldest first, including revoked ones. The secret key
        itself is never returned again; `prefix` tells keys apart.

        Args:
            amount: Default: 50.

        Returns:
            An async iterator over APIKey, which requests each page as it is reached.

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        if amount is not None:
            kwargs["amount"] = amount

        return _async_pages(list_api_keys.asyncio_detailed, kwargs)

    async def list_page(
        self,
        *,
        amount: int | None = None,
        page: str | None = None,
    ) -> APIKeyPage:
        """List API keys: one page.

        Lists the authenticated account's API keys, oldest first, including revoked ones. The secret key
        itself is never returned again; `prefix` tells keys apart.

        Args:
            amount: Default: 50.
            page: The ``pagination.next_page_id`` of the previous page; the first page without it.

        Returns:
            APIKeyPage

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        if amount is not None:
            kwargs["amount"] = amount

        if page is not None:
            kwargs["page"] = page
        response = await list_api_keys.asyncio_detailed(**kwargs)
        return cast(APIKeyPage, response.parsed)

    async def create(
        self,
        *,
        name: str,
        permissions: builtins.list[
            Literal[
                "search",
                "read",
                "write",
                "create_index",
                "manage_index",
                "manage_members",
                "manage_organization",
            ]
        ],
        organization: str | None = None,
        indexes: builtins.list[str] | None = None,
        expires_at: datetime.datetime | None = None,
    ) -> APIKeyCreated:
        """Create an API key

        Creates a key that reaches one organization or all of the account's, a list of indexes or all of
        them, with a set of permissions, until it expires. A 404 means the organization or an index
        named does not exist or is not visible. Only a signed-in session can create, list or revoke
        keys. The response is the only time the secret key is shown, so store it securely. Send it as a
        bearer token: `Authorization: Bearer <key>`.

        Args:
            name: A name to tell the key apart, 1 to 128 characters.
            permissions: The permissions a key carries, each named once. Each one of ``"search"``,
                ``"read"``, ``"write"``, ``"create_index"``, ``"manage_index"``, ``"manage_members"``,
                ``"manage_organization"``.
            organization: An account or organization name. Accounts and organizations share one
                namespace. A name keeps the case it was created with, and any spelling that differs only in
                case refers to it; no other account or organization can take such a spelling.
            indexes: The indexes a key reaches, by name, in the key's one organization. Omitted for
                every index of its organizations, including indexes created later. A request names at least
                one; a key's list is empty once every index it named is deleted.
            expires_at: When the key stops working, at most one year ahead. Omitted for a key that never
                expires.

        Returns:
            APIKeyCreated

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        fields: dict[str, Any] = {}
        fields["name"] = name
        fields["permissions"] = [Permission(item) for item in permissions]
        if organization is not None:
            fields["organization"] = organization
        if indexes is not None:
            fields["indexes"] = indexes
        if expires_at is not None:
            fields["expires_at"] = expires_at
        kwargs["body"] = CreateAPIKeyRequest(**fields)

        response = await create_api_key.asyncio_detailed(**kwargs)
        return cast(APIKeyCreated, response.parsed)

    async def revoke(
        self,
        api_key_id: UUID,
    ) -> None:
        """Revoke an API key

        Revokes one of the authenticated account's API keys. Requests authenticated with it are refused
        from then on. A key that doesn't exist or belongs to another account is not found.

        Args:
            api_key_id:

        Returns:
            None

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        kwargs["api_key_id"] = api_key_id

        await revoke_api_key.asyncio_detailed(**kwargs)


class AsyncAccount:
    """User accounts: registration, sign-in and the current user."""

    def __init__(self, client: Client) -> None:
        self._client = client

    async def register(
        self,
        *,
        name: str,
        email: str,
        password: str,
        invitation: str | None = None,
    ) -> User:
        """Register a local user

        A 409 has code `username_taken` when an account or an organization already holds the username,
        and code `email_taken` when an account already uses the email address. A 403 has code
        `invitation_required` when registration is by invitation and the request carries none, and code
        `invitation_invalid` when the invitation it carries was already used, was withdrawn or has
        expired. A valid invitation is accepted with the registration, and the account joins the
        organization it names, if any.

        Args:
            name: An account or organization name. Accounts and organizations share one namespace. A
                name keeps the case it was created with, and any spelling that differs only in case refers
                to it; no other account or organization can take such a spelling.
            email: The account's email address, at most 320 characters. No other account can use it.
            password: The password, 12 to 1,024 characters.
            invitation: The token of the invitation link the account was invited with. Required when
                registration is by invitation.

        Returns:
            User

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        fields: dict[str, Any] = {}
        fields["name"] = name
        fields["email"] = email
        fields["password"] = password
        if invitation is not None:
            fields["invitation"] = invitation
        kwargs["body"] = RegisterRequest(**fields)

        response = await register_user.asyncio_detailed(**kwargs)
        return cast(User, response.parsed)

    async def auth_options(
        self,
    ) -> AuthOptions:
        """Get the sign-in options

        How accounts are created on this service. The console reads it to decide whether to offer
        registration without an invitation.

        Returns:
            AuthOptions

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}

        response = await get_auth_options.asyncio_detailed(**kwargs)
        return cast(AuthOptions, response.parsed)

    async def check_invitation(
        self,
        *,
        token: str,
    ) -> InvitationPreview:
        """Check an invitation

        Reports what a pending invitation offers, so the registration form can show it. The token
        travels in the body, never in the URL. An invitation that was used, withdrawn or has expired is
        not found.

        Args:
            token: The token from the invitation link.

        Returns:
            InvitationPreview

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        fields: dict[str, Any] = {}
        fields["token"] = token
        kwargs["body"] = InvitationCheckRequest(**fields)

        response = await check_invitation.asyncio_detailed(**kwargs)
        return cast(InvitationPreview, response.parsed)

    async def username_availability(
        self,
        name: str,
    ) -> UsernameAvailability:
        """Check whether a username is available

        Reports whether an account can register this username now. Accounts and organizations share one
        namespace, so a name either one holds, in any case, is taken. The answer can change before the
        name is registered.

        Args:
            name: An account or organization name. Accounts and organizations share one namespace. A
                name keeps the case it was created with, and any spelling that differs only in case refers
                to it; no other account or organization can take such a spelling.

        Returns:
            UsernameAvailability

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        kwargs["name"] = name

        response = await get_username_availability.asyncio_detailed(**kwargs)
        return cast(UsernameAvailability, response.parsed)

    async def login(
        self,
        *,
        identifier: str,
        password: str,
    ) -> User:
        """Create a user session

        Signs in with a username or email address and a password, and starts a browser session: the
        response sets the session cookie and returns, in X-Csrf-Token, the token every state change made
        with that cookie must send. A 401 means the credentials were not accepted. Programs authenticate
        with an API key instead.

        Args:
            identifier: A username or an email address, matched case-insensitively.
            password: The account's password.

        Returns:
            User

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        fields: dict[str, Any] = {}
        fields["identifier"] = identifier
        fields["password"] = password
        kwargs["body"] = LoginRequest(**fields)

        response = await login.asyncio_detailed(**kwargs)
        return cast(User, response.parsed)

    async def logout(
        self,
    ) -> None:
        """Revoke the current session

        Ends the session that made the request and clears its cookie. Other sessions and API keys are
        unaffected.

        Returns:
            None

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}

        await logout.asyncio_detailed(**kwargs)

    async def me(
        self,
    ) -> User:
        """Get the current user

        Returns the account the request authenticates as, whether with a session or an API key. A
        session request also receives its CSRF token in X-Csrf-Token.

        Returns:
            User

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}

        response = await get_current_user.asyncio_detailed(**kwargs)
        return cast(User, response.parsed)

    async def change_password(
        self,
        *,
        current_password: str,
        new_password: str,
    ) -> None:
        """Change the current password

        Changes the signed-in account's password after checking the current one. Every other session of
        the account is signed out; the session that made the request stays signed in, and API keys keep
        working. A 401 means the current password was wrong.

        Args:
            current_password: The account's current password.
            new_password: The new password, 12 to 1,024 characters.

        Returns:
            None

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        fields: dict[str, Any] = {}
        fields["current_password"] = current_password
        fields["new_password"] = new_password
        kwargs["body"] = ChangePasswordRequest(**fields)

        await change_password.asyncio_detailed(**kwargs)


class AsyncDeviceLogin:
    """Device login: obtain an API key by approving a code in the browser."""

    def __init__(self, client: Client) -> None:
        self._client = client

    async def start(
        self,
        *,
        api_key_name: str,
        permissions: builtins.list[
            Literal[
                "search",
                "read",
                "write",
                "create_index",
                "manage_index",
                "manage_members",
                "manage_organization",
            ]
        ],
        organization: str | None = None,
        indexes: builtins.list[str] | None = None,
        expires_at: datetime.datetime | None = None,
    ) -> DeviceAuthorization:
        """Start device authorization

        Starts signing in a device, such as the command-line client, without entering a password on it.
        Show the user `user_code` and send them to `verification_uri` (or `verification_uri_complete`)
        to approve it in a signed-in browser, then poll for the API key with `device_code`. The
        authorization expires after `expires_in` seconds.

        Args:
            api_key_name: The name to give the API key the device receives, 1 to 128 characters.
            permissions: The permissions a key carries, each named once. Each one of ``"search"``,
                ``"read"``, ``"write"``, ``"create_index"``, ``"manage_index"``, ``"manage_members"``,
                ``"manage_organization"``.
            organization: An account or organization name. Accounts and organizations share one
                namespace. A name keeps the case it was created with, and any spelling that differs only in
                case refers to it; no other account or organization can take such a spelling.
            indexes: The indexes a key reaches, by name, in the key's one organization. Omitted for
                every index of its organizations, including indexes created later. A request names at least
                one; a key's list is empty once every index it named is deleted.
            expires_at: When the key stops working, at most one year ahead. Omitted for a key that never
                expires.

        Returns:
            DeviceAuthorization

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        fields: dict[str, Any] = {}
        fields["api_key_name"] = api_key_name
        fields["permissions"] = [Permission(item) for item in permissions]
        if organization is not None:
            fields["organization"] = organization
        if indexes is not None:
            fields["indexes"] = indexes
        if expires_at is not None:
            fields["expires_at"] = expires_at
        kwargs["body"] = DeviceAuthorizationRequest(**fields)

        response = await start_device_authorization.asyncio_detailed(**kwargs)
        return cast(DeviceAuthorization, response.parsed)

    async def approve(
        self,
        *,
        user_code: str,
        scope: KeyScope | None = None,
    ) -> None:
        """Approve device authorization

        Approves a pending device authorization, identified by the code the device shows. The device's
        next poll receives a new API key with the name it asked for. Without a scope it grants what the
        device asked for; a scope replaces that as a whole, narrower or wider. The key never does more
        than the approving account can. A code that is unknown, already decided or expired is not found.
        Only a signed-in session can approve.

        Args:
            user_code: The code the device shows. Hyphens, surrounding spaces and case are ignored.
            scope: What a key reaches and may do. A field left out sets no limit.

        Returns:
            None

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        fields: dict[str, Any] = {}
        fields["user_code"] = user_code
        if scope is not None:
            fields["scope"] = scope
        kwargs["body"] = DeviceApprovalRequest(**fields)

        await approve_device_authorization.asyncio_detailed(**kwargs)

    async def deny(
        self,
        *,
        user_code: str,
    ) -> None:
        """Deny device authorization

        Denies a pending device authorization, identified by the code the device shows. The device's
        next poll fails with code `access_denied`. A code that is unknown, already decided or expired is
        not found.

        Args:
            user_code: The code the device shows. Hyphens, surrounding spaces and case are ignored.

        Returns:
            None

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        fields: dict[str, Any] = {}
        fields["user_code"] = user_code
        kwargs["body"] = DeviceDecisionRequest(**fields)

        await deny_device_authorization.asyncio_detailed(**kwargs)

    async def poll(
        self,
        *,
        device_code: str,
    ) -> APIKeyCreated:
        """Poll for a device API key

        Exchanges an approved device code for an API key, once. Until the user decides, a poll fails
        with 400 and code `authorization_pending`: poll again after `interval` seconds. Polling sooner
        fails with `slow_down` and adds 5 seconds to the interval. A denied authorization fails with
        `access_denied`, and an unknown, expired or already used code with `expired_token`.

        Args:
            device_code: The `device_code` from starting the authorization.

        Returns:
            APIKeyCreated

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        fields: dict[str, Any] = {}
        fields["device_code"] = device_code
        kwargs["body"] = DeviceTokenRequest(**fields)

        response = await poll_device_token.asyncio_detailed(**kwargs)
        return cast(APIKeyCreated, response.parsed)

    async def get(
        self,
        *,
        user_code: str,
    ) -> PendingDeviceAuthorization:
        """Read a pending device authorization

        Returns the scope a pending device authorization asks for. Only a signed-in session can read
        one.

        Args:
            user_code: The code the device shows. Hyphens, surrounding spaces and case are ignored.

        Returns:
            PendingDeviceAuthorization

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        fields: dict[str, Any] = {}
        fields["user_code"] = user_code
        kwargs["body"] = DeviceDecisionRequest(**fields)

        response = await get_device_authorization.asyncio_detailed(**kwargs)
        return cast(PendingDeviceAuthorization, response.parsed)


class AsyncConnections:
    """Apps the signed-in user connected through OAuth sign-in, such as MCP clients."""

    def __init__(self, client: Client) -> None:
        self._client = client

    async def list(
        self,
    ) -> ConnectionPage:
        """List connections

        Lists the apps you have connected that are still in use: revoked and ended connections are left
        out. Newest first. Only a signed-in session can list them.

        Returns:
            ConnectionPage

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}

        response = await list_connections.asyncio_detailed(**kwargs)
        return cast(ConnectionPage, response.parsed)

    async def revoke(
        self,
        connection_id: UUID,
    ) -> None:
        """Revoke a connection

        Revokes one of the authenticated account's connections. The app's requests are refused from then
        on, and it must sign in again. A connection that doesn't exist, is already revoked or belongs to
        another account is not found. Only a signed-in session can revoke one.

        Args:
            connection_id:

        Returns:
            None

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        kwargs["connection_id"] = connection_id

        await revoke_connection.asyncio_detailed(**kwargs)


class _GeneratedAsyncClient:
    """The API's resources."""

    organizations: AsyncOrganizations
    indexes: AsyncIndexes
    documents: AsyncDocuments
    search: AsyncSearch
    api_keys: AsyncAPIKeys
    account: AsyncAccount
    device_login: AsyncDeviceLogin
    connections: AsyncConnections

    def __init__(self, client: Client) -> None:
        self._client = client
        self.organizations = AsyncOrganizations(client)
        self.indexes = AsyncIndexes(client)
        self.documents = AsyncDocuments(client)
        self.search = AsyncSearch(client)
        self.api_keys = AsyncAPIKeys(client)
        self.account = AsyncAccount(client)
        self.device_login = AsyncDeviceLogin(client)
        self.connections = AsyncConnections(client)


class _AsyncIndexClient:
    """One index: its documents, search and settings. Make one with ``client.index("organization/index")``."""

    def __init__(self, client: Client, organization: str, index: str) -> None:
        self._client = client
        self._organization = organization
        self._index = index

    def search(
        self,
        *,
        pattern: str,
        mode: Literal["regex", "literal"] | None = None,
        case_sensitive: bool | None = None,
        whole_word: bool | None = None,
        multiline: bool | None = None,
        filter: str | None = None,
        lines_before: int | None = None,
        lines_after: int | None = None,
        amount: int | None = None,
    ) -> AsyncIterator[QueryResult]:
        """Search an index: every result, page after page.

        Searches every searchable document in the index for a regular expression or literal text, and
        returns each match with the lines it covers, sorted by key, then line, then offset. A metadata
        filter restricts the search to matching documents, and context lines can be returned around each
        result. A pattern or filter that doesn't parse is rejected with 400 and code `invalid_pattern`
        or `invalid_filter`.

        Args:
            pattern: What to search for: an RE2 regular expression, or literal text when `mode` is
                `literal`. Required; at most 8,192 characters of valid UTF-8.
            mode: How to read the pattern: `regex` (the default) for RE2 syntax, without backreferences
                or lookaround, or `literal` to match its bytes exactly, with no escaping needed. One of
                ``"regex"``, ``"literal"``.
            case_sensitive: Whether case must match. Defaults to true. False matches under Unicode
                simple case folding; in a regex, `(?i)` does the same for part of the pattern.
            whole_word: Match only where the characters on either side of the match aren't word
                characters: letters, digits or `_`. Defaults to false. Valid only in literal mode.
            multiline: Let a match span lines. Without it a pattern matches within one line, `^` and `$`
                mark the line's edges, and a character class never matches a line break; a pattern that
                contains a line break is rejected. With it the pattern is matched against the whole
                document, `^` and `$` still mark line edges, `\\A` and `\\z` mark the document's edges, and
                a match may contain line breaks. Default: False.
            filter: Search only the documents whose metadata matches this expression, such as `path
                STARTSWITH 'src/' AND size < 1048576`. At most 8,192 characters. Omit it to search every
                document.
            lines_before: How many lines before each result to return with it, from the same document.
                Default: 0.
            lines_after: How many lines after each result to return with it, from the same document.
                Default: 0.
            amount: Default: 50.

        Returns:
            An async iterator over QueryResult, which requests each page as it is reached.

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        kwargs["organization"] = self._organization
        kwargs["index"] = self._index
        if amount is not None:
            kwargs["amount"] = amount
        fields: dict[str, Any] = {}
        fields["pattern"] = pattern
        if mode is not None:
            fields["mode"] = QueryRequestMode(mode)
        if case_sensitive is not None:
            fields["case_sensitive"] = case_sensitive
        if whole_word is not None:
            fields["whole_word"] = whole_word
        if multiline is not None:
            fields["multiline"] = multiline
        if filter is not None:
            fields["filter_"] = filter
        if lines_before is not None:
            fields["lines_before"] = lines_before
        if lines_after is not None:
            fields["lines_after"] = lines_after
        kwargs["body"] = QueryRequest(**fields)

        return _async_pages(query_index.asyncio_detailed, kwargs)

    async def search_page(
        self,
        *,
        pattern: str,
        mode: Literal["regex", "literal"] | None = None,
        case_sensitive: bool | None = None,
        whole_word: bool | None = None,
        multiline: bool | None = None,
        filter: str | None = None,
        lines_before: int | None = None,
        lines_after: int | None = None,
        amount: int | None = None,
        page: str | None = None,
    ) -> QueryPage:
        """Search an index: one page.

        Searches every searchable document in the index for a regular expression or literal text, and
        returns each match with the lines it covers, sorted by key, then line, then offset. A metadata
        filter restricts the search to matching documents, and context lines can be returned around each
        result. A pattern or filter that doesn't parse is rejected with 400 and code `invalid_pattern`
        or `invalid_filter`. Continue with `page` while `has_next` is true: a page can be empty while
        more results follow.

        Args:
            pattern: What to search for: an RE2 regular expression, or literal text when `mode` is
                `literal`. Required; at most 8,192 characters of valid UTF-8.
            mode: How to read the pattern: `regex` (the default) for RE2 syntax, without backreferences
                or lookaround, or `literal` to match its bytes exactly, with no escaping needed. One of
                ``"regex"``, ``"literal"``.
            case_sensitive: Whether case must match. Defaults to true. False matches under Unicode
                simple case folding; in a regex, `(?i)` does the same for part of the pattern.
            whole_word: Match only where the characters on either side of the match aren't word
                characters: letters, digits or `_`. Defaults to false. Valid only in literal mode.
            multiline: Let a match span lines. Without it a pattern matches within one line, `^` and `$`
                mark the line's edges, and a character class never matches a line break; a pattern that
                contains a line break is rejected. With it the pattern is matched against the whole
                document, `^` and `$` still mark line edges, `\\A` and `\\z` mark the document's edges, and
                a match may contain line breaks. Default: False.
            filter: Search only the documents whose metadata matches this expression, such as `path
                STARTSWITH 'src/' AND size < 1048576`. At most 8,192 characters. Omit it to search every
                document.
            lines_before: How many lines before each result to return with it, from the same document.
                Default: 0.
            lines_after: How many lines after each result to return with it, from the same document.
                Default: 0.
            amount: Default: 50.
            page: The ``pagination.next_page_id`` of the previous page; the first page without it.

        Returns:
            QueryPage

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        kwargs["organization"] = self._organization
        kwargs["index"] = self._index
        if amount is not None:
            kwargs["amount"] = amount
        fields: dict[str, Any] = {}
        fields["pattern"] = pattern
        if mode is not None:
            fields["mode"] = QueryRequestMode(mode)
        if case_sensitive is not None:
            fields["case_sensitive"] = case_sensitive
        if whole_word is not None:
            fields["whole_word"] = whole_word
        if multiline is not None:
            fields["multiline"] = multiline
        if filter is not None:
            fields["filter_"] = filter
        if lines_before is not None:
            fields["lines_before"] = lines_before
        if lines_after is not None:
            fields["lines_after"] = lines_after
        kwargs["body"] = QueryRequest(**fields)

        if page is not None:
            kwargs["page"] = page
        response = await query_index.asyncio_detailed(**kwargs)
        return cast(QueryPage, response.parsed)

    async def list_page(
        self,
        *,
        amount: int | None = None,
        prefix: str | None = None,
        delimiter: str | None = None,
        page: str | None = None,
    ) -> DocumentPage:
        """List documents: one page.

        Lists documents in key byte order, with each one's revision, size, metadata and whether a search
        can match it. Narrow the listing with `prefix`, and add `delimiter` to browse keys like a
        directory tree: keys that share the part up to the next delimiter are returned once, in
        `common_prefixes`.

        Args:
            amount: Default: 50.
            prefix:
            delimiter:
            page: The ``pagination.next_page_id`` of the previous page; the first page without it.

        Returns:
            DocumentPage

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        kwargs["organization"] = self._organization
        kwargs["index"] = self._index
        if amount is not None:
            kwargs["amount"] = amount
        if prefix is not None:
            kwargs["prefix"] = prefix
        if delimiter is not None:
            kwargs["delimiter"] = delimiter

        if page is not None:
            kwargs["page"] = page
        response = await list_documents.asyncio_detailed(**kwargs)
        return cast(DocumentPage, response.parsed)

    async def get(
        self,
        key: str,
        *,
        range: str | None = None,
    ) -> File:
        """Get a document

        Returns a document's content exactly as it was stored, its revision in the ETag header and its
        metadata in the X-Grepvine-Metadata header. Send a Range header to read one byte range; the
        response is then 206, or 416 when the range lies outside the document.

        Args:
            key:
            range:

        Returns:
            File

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        kwargs["organization"] = self._organization
        kwargs["index"] = self._index
        kwargs["key"] = key
        if range is not None:
            kwargs["range_"] = range

        response = await get_document.asyncio_detailed(**kwargs)
        return cast(File, response.parsed)

    async def _put(
        self,
        *,
        key: str,
        content: File,
        metadata: Metadata
        | Mapping[
            str,
            bool
            | int
            | str
            | TaggedBooleanMetadataValue
            | TaggedIntegerMetadataValue
            | TaggedNumberMetadataValue
            | TaggedStringMetadataValue
            | TaggedTimestampMetadataValue,
        ]
        | None = None,
        idempotency_key: str | None = None,
        if_match: str | None = None,
        if_none_match: Literal["*"] | None = None,
    ) -> MutationResult:
        """Store one document

        Stores one document of at most 1 GiB. Content that is valid UTF-8 and at most 100 MiB is
        searchable. Any other content, such as an image or a larger file, is stored, listed, and served
        by the document endpoints but is never matched by a search. The `searchable` field of a listing
        reports which applies.

        Args:
            key: The document's key: a UTF-8, POSIX-style path of at most 1,024 bytes, with no empty,
                `.` or `..` components. Storing a key that exists replaces that document.
            content: The document bytes, at most 1 GiB. Valid UTF-8 of at most 100 MiB is searchable;
                other content is stored without being searchable.
            metadata: Document metadata as a request sends it. Values are plain or tagged.
            idempotency_key:
            if_match:
            if_none_match: One of ``"*"``.

        Returns:
            MutationResult

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        kwargs["organization"] = self._organization
        kwargs["index"] = self._index
        if idempotency_key is not None:
            kwargs["idempotency_key"] = idempotency_key
        if if_match is not None:
            kwargs["if_match"] = if_match
        if if_none_match is not None:
            kwargs["if_none_match"] = PutDocumentIfNoneMatch(if_none_match)
        fields: dict[str, Any] = {}
        fields["key"] = key
        fields["content"] = content
        if metadata is not None:
            fields["metadata"] = _model(Metadata, metadata)
        kwargs["body"] = PutDocumentForm(**fields)

        response = await put_document.asyncio_detailed(**kwargs)
        return cast(MutationResult, response.parsed)

    async def delete(
        self,
        key: str,
        *,
        idempotency_key: str | None = None,
        if_match: str | None = None,
    ) -> MutationResult:
        """Delete one document

        Deletes one document. Send If-Match with a revision to delete it only if it still has that
        revision. Retrying with the same Idempotency-Key returns the original result. Once acknowledged,
        the document no longer matches any search.

        Args:
            key:
            idempotency_key:
            if_match:

        Returns:
            MutationResult

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        kwargs["organization"] = self._organization
        kwargs["index"] = self._index
        kwargs["key"] = key
        if idempotency_key is not None:
            kwargs["idempotency_key"] = idempotency_key
        if if_match is not None:
            kwargs["if_match"] = if_match

        response = await delete_document.asyncio_detailed(**kwargs)
        return cast(MutationResult, response.parsed)

    async def _put_batch(
        self,
        *,
        body: File,
        idempotency_key: str | None = None,
    ) -> MutationBatchResult:
        """Store a batch of documents

        Stores up to 2,048 documents. Each document is stored on its own: a document whose precondition
        fails is not stored, the others are, and the result of each document says which happened.
        Retrying
        with the same Idempotency-Key returns the same results and stores any document an interrupted
        attempt did not reach. Batch content is text carried as JSON strings, so every document stored
        this
        way is searchable. Store binary content, or a document over 16 MiB, with the
        single-document endpoint. The body may be sent with `Content-Encoding: gzip`; the service
        decodes it
        before applying the limits below, and answers any other content encoding with 415
        `unsupported_content_encoding`.

        Args:
            idempotency_key:

        Returns:
            MutationBatchResult

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        kwargs["organization"] = self._organization
        kwargs["index"] = self._index
        if idempotency_key is not None:
            kwargs["idempotency_key"] = idempotency_key
        kwargs["body"] = body

        response = await put_objects.asyncio_detailed(**kwargs)
        return cast(MutationBatchResult, response.parsed)

    async def delete_batch(
        self,
        *,
        objects: builtins.list[DeleteObjectRecord | Mapping[str, Any]],
        idempotency_key: str | None = None,
    ) -> MutationBatchResult:
        """Delete a batch of documents

        Deletes up to 2,048 documents. Each document is deleted on its own: a document that does not
        exist or whose precondition fails is not deleted, the others are, and the result of each
        document
        says which happened. Retrying with the same Idempotency-Key returns the same results.

        Args:
            objects: The documents to delete, 1 to 2,048.
            idempotency_key:

        Returns:
            MutationBatchResult

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        kwargs["organization"] = self._organization
        kwargs["index"] = self._index
        if idempotency_key is not None:
            kwargs["idempotency_key"] = idempotency_key
        fields: dict[str, Any] = {}
        fields["objects"] = [_model(DeleteObjectRecord, item) for item in objects]
        kwargs["body"] = DeleteObjectsRequest(**fields)

        response = await delete_objects.asyncio_detailed(**kwargs)
        return cast(MutationBatchResult, response.parsed)

    async def create(
        self,
        *,
        description: str | None = None,
        tags: IndexTags | Mapping[str, str] | None = None,
    ) -> AsyncIndexCreation:
        """Create an index

        Creates an empty index. Requires the owner or admin role. A new index is usually `ready` in the
        response; if it is still `creating`, read it until it is `ready`. A 409 means the organization
        already has an index with that name, in any case.

        Args:
            description: What the index holds, in Markdown. Empty when no description was set. Clients
                render it without raw HTML.
            tags: Key/value labels on the index, for example the commit it was synced from. At most 64
                tags. A key is 1 to 128 characters without whitespace or control characters; a value is at
                most 1,024 characters without control characters. Empty when none was set.

        Returns:
            AsyncIndexCreation: the answer as ``result``, and ``wait()`` to wait until the work is done.

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        kwargs["organization"] = self._organization
        fields: dict[str, Any] = {}
        fields["name"] = self._index
        if description is not None:
            fields["description"] = description
        if tags is not None:
            fields["tags"] = _model(IndexTags, tags)
        kwargs["body"] = CreateIndexRequest(**fields)

        response = await create_index.asyncio_detailed(**kwargs)
        source = {**kwargs, **fields}
        polled = {
            "organization": source["organization"],
            "index": source["name"],
        }
        return AsyncIndexCreation(
            response.parsed,
            get_index.asyncio_detailed,
            {"client": self._client, **polled},
            "index " + "/".join(polled.values()),
        )

    async def info(
        self,
    ) -> Index:
        """Get an index

        Returns one index with its current state, document count and size, and the progress of its
        background optimization while one runs. Any member can read it.

        Returns:
            Index

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        kwargs["organization"] = self._organization
        kwargs["index"] = self._index

        response = await get_index.asyncio_detailed(**kwargs)
        return cast(Index, response.parsed)

    async def update(
        self,
        *,
        description: str | None = None,
        tags: IndexTagChanges | Mapping[str, None | str] | None = None,
    ) -> Index:
        """Update an index

        Changes the index's description or tags. A field absent from the request is left as it is. The
        name is immutable.

        Args:
            description: What the index holds, in Markdown. Empty when no description was set. Clients
                render it without raw HTML.
            tags: Tags to set, by key, and tags to remove, given as null. A key absent from the map is
                unchanged.

        Returns:
            Index

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        kwargs["organization"] = self._organization
        kwargs["index"] = self._index
        fields: dict[str, Any] = {}
        if description is not None:
            fields["description"] = description
        if tags is not None:
            fields["tags"] = _model(IndexTagChanges, tags)
        kwargs["body"] = UpdateIndexRequest(**fields)

        response = await update_index.asyncio_detailed(**kwargs)
        return cast(Index, response.parsed)

    async def delete_index(
        self,
    ) -> AsyncIndexDeletion:
        """Delete an index

        Starts deleting an index and all its documents. Requires the owner or admin role. The index is
        `deleting` until the deletion finishes in the background, and it can't be undone.

        Returns:
            AsyncIndexDeletion: the answer as ``result``, and ``wait()`` to wait until the work is done.

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.
        """
        kwargs: dict[str, Any] = {"client": self._client}
        kwargs["organization"] = self._organization
        kwargs["index"] = self._index

        response = await delete_index.asyncio_detailed(**kwargs)
        source = kwargs
        polled = {
            "organization": source["organization"],
            "index": source["index"],
        }
        return AsyncIndexDeletion(
            response.parsed,
            get_index.asyncio_detailed,
            {"client": self._client, **polled},
            "index " + "/".join(polled.values()),
        )
