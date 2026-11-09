"""Resource classes for every API operation, one method per operation."""

from typing import cast

from ..client import Client
from ..models.add_member_request import AddMemberRequest
from ..models.api_key_created import APIKeyCreated
from ..models.api_key_page import APIKeyPage
from ..models.auth_options import AuthOptions
from ..models.change_password_request import ChangePasswordRequest
from ..models.create_api_key_request import CreateAPIKeyRequest
from ..models.create_index_request import CreateIndexRequest
from ..models.create_organization_request import CreateOrganizationRequest
from ..models.delete_objects_request import DeleteObjectsRequest
from ..models.device_authorization import DeviceAuthorization
from ..models.device_authorization_request import DeviceAuthorizationRequest
from ..models.device_decision_request import DeviceDecisionRequest
from ..models.device_token_request import DeviceTokenRequest
from ..models.document_page import DocumentPage
from ..models.index import Index
from ..models.index_page import IndexPage
from ..models.invitation_check_request import InvitationCheckRequest
from ..models.invitation_preview import InvitationPreview
from ..models.login_request import LoginRequest
from ..models.member import Member
from ..models.member_page import MemberPage
from ..models.mutation_batch_result import MutationBatchResult
from ..models.mutation_result import MutationResult
from ..models.organization import Organization
from ..models.organization_page import OrganizationPage
from ..models.put_document_form import PutDocumentForm
from ..models.put_document_if_none_match import PutDocumentIfNoneMatch
from ..models.query_page import QueryPage
from ..models.query_request import QueryRequest
from ..models.register_request import RegisterRequest
from ..models.transfer_ownership_request import TransferOwnershipRequest
from ..models.update_index_request import UpdateIndexRequest
from ..models.update_member_request import UpdateMemberRequest
from ..models.user import User
from ..models.username_availability import UsernameAvailability
from ..types import File
from ..types import UNSET, Unset
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
from .device_login import approve_device_authorization
from .device_login import deny_device_authorization
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


class Members:
    """The members of an organization and their roles."""

    def __init__(self, client: Client) -> None:
        self._client = client

    def list(
        self,
        organization: str,
        *,
        amount: int | Unset = 50,
        page: str | Unset = UNSET,
    ) -> MemberPage:
        """List organization members

         Lists an organization's members and their roles, ordered by name. Requires the owner or admin role.

        Args:
            organization (str): An account or organization name. Accounts and organizations share one
                namespace. A name keeps the case it was created with, and any spelling that differs only
                in case refers to it; no other account or organization can take such a spelling.
            amount (int | Unset):  Default: 50.
            page (str | Unset):

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.

        Returns:
            MemberPage
        """

        response = list_organization_members.sync_detailed(
            organization=organization,
            amount=amount,
            page=page,
            client=self._client,
        )
        return cast(MemberPage, response.parsed)

    def add(
        self,
        organization: str,
        *,
        body: AddMemberRequest,
    ) -> Member:
        """Add an organization member

         Adds an existing account to the organization with the admin, developer or reader role. Requires the
        owner or admin role. An organization has one owner, changed only by transferring ownership.

        Args:
            organization (str): An account or organization name. Accounts and organizations share one
                namespace. A name keeps the case it was created with, and any spelling that differs only
                in case refers to it; no other account or organization can take such a spelling.
            body (AddMemberRequest): The account to add and its role.

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.

        Returns:
            Member
        """

        response = add_organization_member.sync_detailed(
            organization=organization,
            body=body,
            client=self._client,
        )
        return cast(Member, response.parsed)

    def update(
        self,
        organization: str,
        user: str,
        *,
        body: UpdateMemberRequest,
    ) -> Member:
        """Change an organization member role

         Changes a member's role to admin, developer or reader. Requires the owner or admin role. The owner's
        role changes only by transferring ownership.

        Args:
            organization (str): An account or organization name. Accounts and organizations share one
                namespace. A name keeps the case it was created with, and any spelling that differs only
                in case refers to it; no other account or organization can take such a spelling.
            user (str): An account or organization name. Accounts and organizations share one
                namespace. A name keeps the case it was created with, and any spelling that differs only
                in case refers to it; no other account or organization can take such a spelling.
            body (UpdateMemberRequest): The member's new role.

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.

        Returns:
            Member
        """

        response = update_organization_member.sync_detailed(
            organization=organization,
            user=user,
            body=body,
            client=self._client,
        )
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
            organization (str): An account or organization name. Accounts and organizations share one
                namespace. A name keeps the case it was created with, and any spelling that differs only
                in case refers to it; no other account or organization can take such a spelling.
            user (str): An account or organization name. Accounts and organizations share one
                namespace. A name keeps the case it was created with, and any spelling that differs only
                in case refers to it; no other account or organization can take such a spelling.

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.

        Returns:
            None
        """

        remove_organization_member.sync_detailed(
            organization=organization,
            user=user,
            client=self._client,
        )


class Organizations:
    """Organizations: create, read, delete and transfer them."""

    members: Members

    def __init__(self, client: Client) -> None:
        self._client = client
        self.members = Members(client)

    def list(
        self,
        *,
        amount: int | Unset = 50,
        page: str | Unset = UNSET,
    ) -> OrganizationPage:
        """List organizations

         Lists the organizations the authenticated account belongs to, with its role in each, ordered by
        name.

        Args:
            amount (int | Unset):  Default: 50.
            page (str | Unset):

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.

        Returns:
            OrganizationPage
        """

        response = list_organizations.sync_detailed(
            amount=amount,
            page=page,
            client=self._client,
        )
        return cast(OrganizationPage, response.parsed)

    def create(
        self,
        *,
        body: CreateOrganizationRequest,
    ) -> Organization:
        """Create an organization

         Creates an organization owned by the authenticated account. Accounts and organizations share one
        namespace, so a 409 means an account or organization already holds the name, in any case.

        Args:
            body (CreateOrganizationRequest): A new organization.

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.

        Returns:
            Organization
        """

        response = create_organization.sync_detailed(
            body=body,
            client=self._client,
        )
        return cast(Organization, response.parsed)

    def get(
        self,
        organization: str,
    ) -> Organization:
        """Get an organization

         Returns an organization the authenticated account belongs to, with its role there. It answers for a
        suspended organization too, and reports `suspended`.

        Args:
            organization (str): An account or organization name. Accounts and organizations share one
                namespace. A name keeps the case it was created with, and any spelling that differs only
                in case refers to it; no other account or organization can take such a spelling.

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.

        Returns:
            Organization
        """

        response = get_organization.sync_detailed(
            organization=organization,
            client=self._client,
        )
        return cast(Organization, response.parsed)

    def delete(
        self,
        organization: str,
    ) -> None:
        """Delete an organization

         Starts deleting an organization with all its indexes and documents. Only the owner can delete it.
        The deletion finishes in the background and can't be undone.

        Args:
            organization (str): An account or organization name. Accounts and organizations share one
                namespace. A name keeps the case it was created with, and any spelling that differs only
                in case refers to it; no other account or organization can take such a spelling.

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.

        Returns:
            None
        """

        delete_organization.sync_detailed(
            organization=organization,
            client=self._client,
        )

    def transfer_ownership(
        self,
        organization: str,
        *,
        body: TransferOwnershipRequest,
    ) -> None:
        """Transfer organization ownership

         Makes another member the owner. Only the owner can transfer ownership, and the previous owner stays
        a member with the admin role. The new owner must already be a member, and not one with time-limited
        access.

        Args:
            organization (str): An account or organization name. Accounts and organizations share one
                namespace. A name keeps the case it was created with, and any spelling that differs only
                in case refers to it; no other account or organization can take such a spelling.
            body (TransferOwnershipRequest): The member who becomes the owner.

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.

        Returns:
            None
        """

        transfer_organization_ownership.sync_detailed(
            organization=organization,
            body=body,
            client=self._client,
        )


class Indexes:
    """Indexes in an organization."""

    def __init__(self, client: Client) -> None:
        self._client = client

    def list(
        self,
        organization: str,
        *,
        amount: int | Unset = 50,
        page: str | Unset = UNSET,
        prefix: str | Unset = UNSET,
    ) -> IndexPage:
        """List indexes

         Lists the organization's indexes, ordered by name. Any member can list them.

        Args:
            organization (str): An account or organization name. Accounts and organizations share one
                namespace. A name keeps the case it was created with, and any spelling that differs only
                in case refers to it; no other account or organization can take such a spelling.
            amount (int | Unset):  Default: 50.
            page (str | Unset):
            prefix (str | Unset):

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.

        Returns:
            IndexPage
        """

        response = list_indexes.sync_detailed(
            organization=organization,
            amount=amount,
            page=page,
            prefix=prefix,
            client=self._client,
        )
        return cast(IndexPage, response.parsed)

    def create(
        self,
        organization: str,
        *,
        body: CreateIndexRequest,
    ) -> Index:
        """Create an index

         Creates an empty index. Requires the owner or admin role. A new index is usually `ready` in the
        response; if it is still `creating`, read it until it is `ready`. A 409 means the organization
        already has an index with that name, in any case.

        Args:
            organization (str): An account or organization name. Accounts and organizations share one
                namespace. A name keeps the case it was created with, and any spelling that differs only
                in case refers to it; no other account or organization can take such a spelling.
            body (CreateIndexRequest): A new index.

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.

        Returns:
            Index
        """

        response = create_index.sync_detailed(
            organization=organization,
            body=body,
            client=self._client,
        )
        return cast(Index, response.parsed)

    def get(
        self,
        organization: str,
        index: str,
    ) -> Index:
        """Get an index

         Returns one index with its current state, document count and size, and the progress of its
        background optimization while one runs. Any member can read it.

        Args:
            organization (str): An account or organization name. Accounts and organizations share one
                namespace. A name keeps the case it was created with, and any spelling that differs only
                in case refers to it; no other account or organization can take such a spelling.
            index (str): An index name, unique in its organization. A name keeps the case it was
                created with, and any spelling that differs only in case refers to it; no other index in
                the organization can take such a spelling.

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.

        Returns:
            Index
        """

        response = get_index.sync_detailed(
            organization=organization,
            index=index,
            client=self._client,
        )
        return cast(Index, response.parsed)

    def update(
        self,
        organization: str,
        index: str,
        *,
        body: UpdateIndexRequest,
    ) -> Index:
        """Update an index

         Changes the index's description or tags. A field absent from the request is left as it is. The name
        is immutable.

        Args:
            organization (str): An account or organization name. Accounts and organizations share one
                namespace. A name keeps the case it was created with, and any spelling that differs only
                in case refers to it; no other account or organization can take such a spelling.
            index (str): An index name, unique in its organization. A name keeps the case it was
                created with, and any spelling that differs only in case refers to it; no other index in
                the organization can take such a spelling.
            body (UpdateIndexRequest): The fields to change. A field that is absent is left as it is;
                at least one must be present.

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.

        Returns:
            Index
        """

        response = update_index.sync_detailed(
            organization=organization,
            index=index,
            body=body,
            client=self._client,
        )
        return cast(Index, response.parsed)

    def delete(
        self,
        organization: str,
        index: str,
    ) -> None:
        """Delete an index

         Starts deleting an index and all its documents. Requires the owner or admin role. The index is
        `deleting` until the deletion finishes in the background, and it can't be undone.

        Args:
            organization (str): An account or organization name. Accounts and organizations share one
                namespace. A name keeps the case it was created with, and any spelling that differs only
                in case refers to it; no other account or organization can take such a spelling.
            index (str): An index name, unique in its organization. A name keeps the case it was
                created with, and any spelling that differs only in case refers to it; no other index in
                the organization can take such a spelling.

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.

        Returns:
            None
        """

        delete_index.sync_detailed(
            organization=organization,
            index=index,
            client=self._client,
        )


class Documents:
    """The documents of an index."""

    def __init__(self, client: Client) -> None:
        self._client = client

    def list(
        self,
        organization: str,
        index: str,
        *,
        amount: int | Unset = 50,
        page: str | Unset = UNSET,
        prefix: str | Unset = UNSET,
        delimiter: str | Unset = UNSET,
    ) -> DocumentPage:
        """List documents

         Lists documents in key byte order, with each one's revision, size, metadata and whether a search can
        match it. Narrow the listing with `prefix`, and add `delimiter` to browse keys like a directory
        tree: keys that share the part up to the next delimiter are returned once, in `common_prefixes`.

        Args:
            organization (str): An account or organization name. Accounts and organizations share one
                namespace. A name keeps the case it was created with, and any spelling that differs only
                in case refers to it; no other account or organization can take such a spelling.
            index (str): An index name, unique in its organization. A name keeps the case it was
                created with, and any spelling that differs only in case refers to it; no other index in
                the organization can take such a spelling.
            amount (int | Unset):  Default: 50.
            page (str | Unset):
            prefix (str | Unset):
            delimiter (str | Unset):

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.

        Returns:
            DocumentPage
        """

        response = list_documents.sync_detailed(
            organization=organization,
            index=index,
            amount=amount,
            page=page,
            prefix=prefix,
            delimiter=delimiter,
            client=self._client,
        )
        return cast(DocumentPage, response.parsed)

    def put(
        self,
        organization: str,
        index: str,
        *,
        body: PutDocumentForm,
        idempotency_key: str | Unset = UNSET,
        if_match: str | Unset = UNSET,
        if_none_match: PutDocumentIfNoneMatch | Unset = UNSET,
    ) -> MutationResult:
        """Store one document

         Stores one document of at most 1 GiB. Content that is valid UTF-8 and at most 100 MiB is
        searchable. Any other content, such as an image or a larger file, is stored, listed, and served
        by the document endpoints but is never matched by a search. The `searchable` field of a listing
        reports which applies.

        Args:
            organization (str): An account or organization name. Accounts and organizations share one
                namespace. A name keeps the case it was created with, and any spelling that differs only
                in case refers to it; no other account or organization can take such a spelling.
            index (str): An index name, unique in its organization. A name keeps the case it was
                created with, and any spelling that differs only in case refers to it; no other index in
                the organization can take such a spelling.
            idempotency_key (str | Unset):
            if_match (str | Unset):
            if_none_match (PutDocumentIfNoneMatch | Unset):
            body (PutDocumentForm): One document to store, sent as multipart form fields.

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.

        Returns:
            MutationResult
        """

        response = put_document.sync_detailed(
            organization=organization,
            index=index,
            body=body,
            idempotency_key=idempotency_key,
            if_match=if_match,
            if_none_match=if_none_match,
            client=self._client,
        )
        return cast(MutationResult, response.parsed)

    def get(
        self,
        organization: str,
        index: str,
        key: str,
        *,
        range_: str | Unset = UNSET,
    ) -> File:
        """Get a document

         Returns a document's content exactly as it was stored, its revision in the ETag header and its
        metadata in the X-Grepvine-Metadata header. Send a Range header to read one byte range; the response
        is then 206, or 416 when the range lies outside the document.

        Args:
            organization (str): An account or organization name. Accounts and organizations share one
                namespace. A name keeps the case it was created with, and any spelling that differs only
                in case refers to it; no other account or organization can take such a spelling.
            index (str): An index name, unique in its organization. A name keeps the case it was
                created with, and any spelling that differs only in case refers to it; no other index in
                the organization can take such a spelling.
            key (str):
            range_ (str | Unset):

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.

        Returns:
            File
        """

        response = get_document.sync_detailed(
            organization=organization,
            index=index,
            key=key,
            range_=range_,
            client=self._client,
        )
        return cast(File, response.parsed)

    def delete(
        self,
        organization: str,
        index: str,
        key: str,
        *,
        idempotency_key: str | Unset = UNSET,
        if_match: str | Unset = UNSET,
    ) -> MutationResult:
        """Delete one document

         Deletes one document. Send If-Match with a revision to delete it only if it still has that revision.
        Retrying with the same Idempotency-Key returns the original result. Once acknowledged, the document
        no longer matches any search.

        Args:
            organization (str): An account or organization name. Accounts and organizations share one
                namespace. A name keeps the case it was created with, and any spelling that differs only
                in case refers to it; no other account or organization can take such a spelling.
            index (str): An index name, unique in its organization. A name keeps the case it was
                created with, and any spelling that differs only in case refers to it; no other index in
                the organization can take such a spelling.
            key (str):
            idempotency_key (str | Unset):
            if_match (str | Unset):

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.

        Returns:
            MutationResult
        """

        response = delete_document.sync_detailed(
            organization=organization,
            index=index,
            key=key,
            idempotency_key=idempotency_key,
            if_match=if_match,
            client=self._client,
        )
        return cast(MutationResult, response.parsed)

    def put_batch(
        self,
        organization: str,
        index: str,
        *,
        body: File,
        idempotency_key: str | Unset = UNSET,
    ) -> MutationBatchResult:
        """Store a batch of documents

         Stores up to 2,048 documents. Each document is stored on its own: a document whose precondition
        fails is not stored, the others are, and the result of each document says which happened. Retrying
        with the same Idempotency-Key returns the same results and stores any document an interrupted
        attempt did not reach. Batch content is text carried as JSON strings, so every document stored this
        way is searchable. Store binary content, or a document over 16 MiB, with the
        single-document endpoint. The body may be sent with `Content-Encoding: gzip`; the service decodes it
        before applying the limits below, and answers any other content encoding with 415
        `unsupported_content_encoding`.

        Args:
            organization (str): An account or organization name. Accounts and organizations share one
                namespace. A name keeps the case it was created with, and any spelling that differs only
                in case refers to it; no other account or organization can take such a spelling.
            index (str): An index name, unique in its organization. A name keeps the case it was
                created with, and any spelling that differs only in case refers to it; no other index in
                the organization can take such a spelling.
            idempotency_key (str | Unset):
            body (File): One PutObjectRecord JSON value per line; at most 2,048 records and 16 MiB of
                combined object content.

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.

        Returns:
            MutationBatchResult
        """

        response = put_objects.sync_detailed(
            organization=organization,
            index=index,
            body=body,
            idempotency_key=idempotency_key,
            client=self._client,
        )
        return cast(MutationBatchResult, response.parsed)

    def delete_batch(
        self,
        organization: str,
        index: str,
        *,
        body: DeleteObjectsRequest,
        idempotency_key: str | Unset = UNSET,
    ) -> MutationBatchResult:
        """Delete a batch of documents

         Deletes up to 2,048 documents. Each document is deleted on its own: a document that does not
        exist or whose precondition fails is not deleted, the others are, and the result of each document
        says which happened. Retrying with the same Idempotency-Key returns the same results.

        Args:
            organization (str): An account or organization name. Accounts and organizations share one
                namespace. A name keeps the case it was created with, and any spelling that differs only
                in case refers to it; no other account or organization can take such a spelling.
            index (str): An index name, unique in its organization. A name keeps the case it was
                created with, and any spelling that differs only in case refers to it; no other index in
                the organization can take such a spelling.
            idempotency_key (str | Unset):
            body (DeleteObjectsRequest): The documents to delete.

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.

        Returns:
            MutationBatchResult
        """

        response = delete_objects.sync_detailed(
            organization=organization,
            index=index,
            body=body,
            idempotency_key=idempotency_key,
            client=self._client,
        )
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
        body: QueryRequest,
        amount: int | Unset = 50,
        page: str | Unset = UNSET,
    ) -> QueryPage:
        """Search an index

         Searches every searchable document in the index for a regular expression or literal text, and
        returns each match with the lines it covers, sorted by key, then line, then offset. A metadata
        filter restricts the search to matching documents, and context lines can be returned around each
        result. A pattern or filter that doesn't parse is rejected with 400 and code `invalid_pattern` or
        `invalid_filter`. Continue with `page` while `has_next` is true: a page can be empty while more
        results follow.

        Args:
            organization (str): An account or organization name. Accounts and organizations share one
                namespace. A name keeps the case it was created with, and any spelling that differs only
                in case refers to it; no other account or organization can take such a spelling.
            index (str): An index name, unique in its organization. A name keeps the case it was
                created with, and any spelling that differs only in case refers to it; no other index in
                the organization can take such a spelling.
            amount (int | Unset):  Default: 50.
            page (str | Unset):
            body (QueryRequest): A search: the pattern, how to match it, which documents to search and
                how much context to return.

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.

        Returns:
            QueryPage
        """

        response = query_index.sync_detailed(
            organization=organization,
            index=index,
            body=body,
            amount=amount,
            page=page,
            client=self._client,
        )
        return cast(QueryPage, response.parsed)


class APIKeys:
    """The API keys of the signed-in user."""

    def __init__(self, client: Client) -> None:
        self._client = client

    def list(
        self,
        *,
        amount: int | Unset = 50,
        page: str | Unset = UNSET,
    ) -> APIKeyPage:
        """List API keys

         Lists the authenticated account's API keys, oldest first, including revoked ones. The secret key
        itself is never returned again; `prefix` tells keys apart.

        Args:
            amount (int | Unset):  Default: 50.
            page (str | Unset):

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.

        Returns:
            APIKeyPage
        """

        response = list_api_keys.sync_detailed(
            amount=amount,
            page=page,
            client=self._client,
        )
        return cast(APIKeyPage, response.parsed)

    def create(
        self,
        *,
        body: CreateAPIKeyRequest,
    ) -> APIKeyCreated:
        """Create an API key

         Creates an API key for the authenticated account. The response is the only time the secret key is
        shown, so store it securely. Send it as a bearer token: `Authorization: Bearer <key>`.

        Args:
            body (CreateAPIKeyRequest): A new API key.

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.

        Returns:
            APIKeyCreated
        """

        response = create_api_key.sync_detailed(
            body=body,
            client=self._client,
        )
        return cast(APIKeyCreated, response.parsed)

    def revoke(
        self,
        api_key_id: UUID,
    ) -> None:
        """Revoke an API key

         Revokes one of the authenticated account's API keys. Requests authenticated with it are refused from
        then on. A key that doesn't exist or belongs to another account is not found.

        Args:
            api_key_id (UUID):

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.

        Returns:
            None
        """

        revoke_api_key.sync_detailed(
            api_key_id=api_key_id,
            client=self._client,
        )


class Account:
    """User accounts: registration, sign-in and the current user."""

    def __init__(self, client: Client) -> None:
        self._client = client

    def register(
        self,
        *,
        body: RegisterRequest,
    ) -> User:
        """Register a local user

         A 409 has code `username_taken` when an account or an organization already holds the username, and
        code `email_taken` when an account already uses the email address. A 403 has code
        `invitation_required` when registration is by invitation and the request carries none, and code
        `invitation_invalid` when the invitation it carries was already used, was withdrawn or has expired.
        A valid invitation is accepted with the registration, and the account joins the organization it
        names, if any.

        Args:
            body (RegisterRequest): A new local account.

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.

        Returns:
            User
        """

        response = register_user.sync_detailed(
            body=body,
            client=self._client,
        )
        return cast(User, response.parsed)

    def auth_options(
        self,
    ) -> AuthOptions:
        """Get the sign-in options

         How accounts are created on this service. The console reads it to decide whether to offer
        registration without an invitation.

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.

        Returns:
            AuthOptions
        """

        response = get_auth_options.sync_detailed(
            client=self._client,
        )
        return cast(AuthOptions, response.parsed)

    def check_invitation(
        self,
        *,
        body: InvitationCheckRequest,
    ) -> InvitationPreview:
        """Check an invitation

         Reports what a pending invitation offers, so the registration form can show it. The token travels in
        the body, never in the URL. An invitation that was used, withdrawn or has expired is not found.

        Args:
            body (InvitationCheckRequest): The invitation to look up.

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.

        Returns:
            InvitationPreview
        """

        response = check_invitation.sync_detailed(
            body=body,
            client=self._client,
        )
        return cast(InvitationPreview, response.parsed)

    def username_availability(
        self,
        name: str,
    ) -> UsernameAvailability:
        """Check whether a username is available

         Reports whether an account can register this username now. Accounts and organizations share one
        namespace, so a name either one holds, in any case, is taken. The answer can change before the name
        is registered.

        Args:
            name (str): An account or organization name. Accounts and organizations share one
                namespace. A name keeps the case it was created with, and any spelling that differs only
                in case refers to it; no other account or organization can take such a spelling.

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.

        Returns:
            UsernameAvailability
        """

        response = get_username_availability.sync_detailed(
            name=name,
            client=self._client,
        )
        return cast(UsernameAvailability, response.parsed)

    def login(
        self,
        *,
        body: LoginRequest,
    ) -> User:
        """Create a user session

         Signs in with a username or email address and a password, and starts a browser session: the response
        sets the session cookie and returns, in X-Csrf-Token, the token every state change made with that
        cookie must send. A 401 means the credentials were not accepted. Programs authenticate with an API
        key instead.

        Args:
            body (LoginRequest): Credentials for a new session.

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.

        Returns:
            User
        """

        response = login.sync_detailed(
            body=body,
            client=self._client,
        )
        return cast(User, response.parsed)

    def logout(
        self,
    ) -> None:
        """Revoke the current session

         Ends the session that made the request and clears its cookie. Other sessions and API keys are
        unaffected.

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.

        Returns:
            None
        """

        logout.sync_detailed(
            client=self._client,
        )

    def me(
        self,
    ) -> User:
        """Get the current user

         Returns the account the request authenticates as, whether with a session or an API key. A session
        request also receives its CSRF token in X-Csrf-Token.

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.

        Returns:
            User
        """

        response = get_current_user.sync_detailed(
            client=self._client,
        )
        return cast(User, response.parsed)

    def change_password(
        self,
        *,
        body: ChangePasswordRequest,
    ) -> None:
        """Change the current password

         Changes the signed-in account's password after checking the current one. Every other session of the
        account is signed out; the session that made the request stays signed in, and API keys keep working.
        A 401 means the current password was wrong.

        Args:
            body (ChangePasswordRequest): The current password and its replacement.

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.

        Returns:
            None
        """

        change_password.sync_detailed(
            body=body,
            client=self._client,
        )


class DeviceLogin:
    """Device login: obtain an API key by approving a code in the browser."""

    def __init__(self, client: Client) -> None:
        self._client = client

    def start(
        self,
        *,
        body: DeviceAuthorizationRequest,
    ) -> DeviceAuthorization:
        """Start device authorization

         Starts signing in a device, such as the command-line client, without entering a password on it. Show
        the user `user_code` and send them to `verification_uri` (or `verification_uri_complete`) to approve
        it in a signed-in browser, then poll for the API key with `device_code`. The authorization expires
        after `expires_in` seconds.

        Args:
            body (DeviceAuthorizationRequest): A request to sign in a device.

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.

        Returns:
            DeviceAuthorization
        """

        response = start_device_authorization.sync_detailed(
            body=body,
            client=self._client,
        )
        return cast(DeviceAuthorization, response.parsed)

    def approve(
        self,
        *,
        body: DeviceDecisionRequest,
    ) -> None:
        """Approve device authorization

         Approves a pending device authorization for the signed-in account, identified by the code the device
        shows. The device's next poll receives a new API key with the name it asked for. A code that is
        unknown, already decided or expired is not found.

        Args:
            body (DeviceDecisionRequest): The device authorization to approve or deny.

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.

        Returns:
            None
        """

        approve_device_authorization.sync_detailed(
            body=body,
            client=self._client,
        )

    def deny(
        self,
        *,
        body: DeviceDecisionRequest,
    ) -> None:
        """Deny device authorization

         Denies a pending device authorization, identified by the code the device shows. The device's next
        poll fails with code `access_denied`. A code that is unknown, already decided or expired is not
        found.

        Args:
            body (DeviceDecisionRequest): The device authorization to approve or deny.

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.

        Returns:
            None
        """

        deny_device_authorization.sync_detailed(
            body=body,
            client=self._client,
        )

    def poll(
        self,
        *,
        body: DeviceTokenRequest,
    ) -> APIKeyCreated:
        """Poll for a device API key

         Exchanges an approved device code for an API key, once. Until the user decides, a poll fails with
        400 and code `authorization_pending`: poll again after `interval` seconds. Polling sooner fails with
        `slow_down` and adds 5 seconds to the interval. A denied authorization fails with `access_denied`,
        and an unknown, expired or already used code with `expired_token`.

        Args:
            body (DeviceTokenRequest): The device code to exchange for an API key.

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.

        Returns:
            APIKeyCreated
        """

        response = poll_device_token.sync_detailed(
            body=body,
            client=self._client,
        )
        return cast(APIKeyCreated, response.parsed)


class _GeneratedClient:
    """The API's resources."""

    organizations: Organizations
    indexes: Indexes
    documents: Documents
    search: Search
    api_keys: APIKeys
    account: Account
    device_login: DeviceLogin

    def __init__(self, client: Client) -> None:
        self._client = client
        self.organizations = Organizations(client)
        self.indexes = Indexes(client)
        self.documents = Documents(client)
        self.search = Search(client)
        self.api_keys = APIKeys(client)
        self.account = Account(client)
        self.device_login = DeviceLogin(client)


class AsyncMembers:
    """The members of an organization and their roles."""

    def __init__(self, client: Client) -> None:
        self._client = client

    async def list(
        self,
        organization: str,
        *,
        amount: int | Unset = 50,
        page: str | Unset = UNSET,
    ) -> MemberPage:
        """List organization members

         Lists an organization's members and their roles, ordered by name. Requires the owner or admin role.

        Args:
            organization (str): An account or organization name. Accounts and organizations share one
                namespace. A name keeps the case it was created with, and any spelling that differs only
                in case refers to it; no other account or organization can take such a spelling.
            amount (int | Unset):  Default: 50.
            page (str | Unset):

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.

        Returns:
            MemberPage
        """

        response = await list_organization_members.asyncio_detailed(
            organization=organization,
            amount=amount,
            page=page,
            client=self._client,
        )
        return cast(MemberPage, response.parsed)

    async def add(
        self,
        organization: str,
        *,
        body: AddMemberRequest,
    ) -> Member:
        """Add an organization member

         Adds an existing account to the organization with the admin, developer or reader role. Requires the
        owner or admin role. An organization has one owner, changed only by transferring ownership.

        Args:
            organization (str): An account or organization name. Accounts and organizations share one
                namespace. A name keeps the case it was created with, and any spelling that differs only
                in case refers to it; no other account or organization can take such a spelling.
            body (AddMemberRequest): The account to add and its role.

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.

        Returns:
            Member
        """

        response = await add_organization_member.asyncio_detailed(
            organization=organization,
            body=body,
            client=self._client,
        )
        return cast(Member, response.parsed)

    async def update(
        self,
        organization: str,
        user: str,
        *,
        body: UpdateMemberRequest,
    ) -> Member:
        """Change an organization member role

         Changes a member's role to admin, developer or reader. Requires the owner or admin role. The owner's
        role changes only by transferring ownership.

        Args:
            organization (str): An account or organization name. Accounts and organizations share one
                namespace. A name keeps the case it was created with, and any spelling that differs only
                in case refers to it; no other account or organization can take such a spelling.
            user (str): An account or organization name. Accounts and organizations share one
                namespace. A name keeps the case it was created with, and any spelling that differs only
                in case refers to it; no other account or organization can take such a spelling.
            body (UpdateMemberRequest): The member's new role.

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.

        Returns:
            Member
        """

        response = await update_organization_member.asyncio_detailed(
            organization=organization,
            user=user,
            body=body,
            client=self._client,
        )
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
            organization (str): An account or organization name. Accounts and organizations share one
                namespace. A name keeps the case it was created with, and any spelling that differs only
                in case refers to it; no other account or organization can take such a spelling.
            user (str): An account or organization name. Accounts and organizations share one
                namespace. A name keeps the case it was created with, and any spelling that differs only
                in case refers to it; no other account or organization can take such a spelling.

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.

        Returns:
            None
        """

        await remove_organization_member.asyncio_detailed(
            organization=organization,
            user=user,
            client=self._client,
        )


class AsyncOrganizations:
    """Organizations: create, read, delete and transfer them."""

    members: AsyncMembers

    def __init__(self, client: Client) -> None:
        self._client = client
        self.members = AsyncMembers(client)

    async def list(
        self,
        *,
        amount: int | Unset = 50,
        page: str | Unset = UNSET,
    ) -> OrganizationPage:
        """List organizations

         Lists the organizations the authenticated account belongs to, with its role in each, ordered by
        name.

        Args:
            amount (int | Unset):  Default: 50.
            page (str | Unset):

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.

        Returns:
            OrganizationPage
        """

        response = await list_organizations.asyncio_detailed(
            amount=amount,
            page=page,
            client=self._client,
        )
        return cast(OrganizationPage, response.parsed)

    async def create(
        self,
        *,
        body: CreateOrganizationRequest,
    ) -> Organization:
        """Create an organization

         Creates an organization owned by the authenticated account. Accounts and organizations share one
        namespace, so a 409 means an account or organization already holds the name, in any case.

        Args:
            body (CreateOrganizationRequest): A new organization.

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.

        Returns:
            Organization
        """

        response = await create_organization.asyncio_detailed(
            body=body,
            client=self._client,
        )
        return cast(Organization, response.parsed)

    async def get(
        self,
        organization: str,
    ) -> Organization:
        """Get an organization

         Returns an organization the authenticated account belongs to, with its role there. It answers for a
        suspended organization too, and reports `suspended`.

        Args:
            organization (str): An account or organization name. Accounts and organizations share one
                namespace. A name keeps the case it was created with, and any spelling that differs only
                in case refers to it; no other account or organization can take such a spelling.

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.

        Returns:
            Organization
        """

        response = await get_organization.asyncio_detailed(
            organization=organization,
            client=self._client,
        )
        return cast(Organization, response.parsed)

    async def delete(
        self,
        organization: str,
    ) -> None:
        """Delete an organization

         Starts deleting an organization with all its indexes and documents. Only the owner can delete it.
        The deletion finishes in the background and can't be undone.

        Args:
            organization (str): An account or organization name. Accounts and organizations share one
                namespace. A name keeps the case it was created with, and any spelling that differs only
                in case refers to it; no other account or organization can take such a spelling.

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.

        Returns:
            None
        """

        await delete_organization.asyncio_detailed(
            organization=organization,
            client=self._client,
        )

    async def transfer_ownership(
        self,
        organization: str,
        *,
        body: TransferOwnershipRequest,
    ) -> None:
        """Transfer organization ownership

         Makes another member the owner. Only the owner can transfer ownership, and the previous owner stays
        a member with the admin role. The new owner must already be a member, and not one with time-limited
        access.

        Args:
            organization (str): An account or organization name. Accounts and organizations share one
                namespace. A name keeps the case it was created with, and any spelling that differs only
                in case refers to it; no other account or organization can take such a spelling.
            body (TransferOwnershipRequest): The member who becomes the owner.

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.

        Returns:
            None
        """

        await transfer_organization_ownership.asyncio_detailed(
            organization=organization,
            body=body,
            client=self._client,
        )


class AsyncIndexes:
    """Indexes in an organization."""

    def __init__(self, client: Client) -> None:
        self._client = client

    async def list(
        self,
        organization: str,
        *,
        amount: int | Unset = 50,
        page: str | Unset = UNSET,
        prefix: str | Unset = UNSET,
    ) -> IndexPage:
        """List indexes

         Lists the organization's indexes, ordered by name. Any member can list them.

        Args:
            organization (str): An account or organization name. Accounts and organizations share one
                namespace. A name keeps the case it was created with, and any spelling that differs only
                in case refers to it; no other account or organization can take such a spelling.
            amount (int | Unset):  Default: 50.
            page (str | Unset):
            prefix (str | Unset):

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.

        Returns:
            IndexPage
        """

        response = await list_indexes.asyncio_detailed(
            organization=organization,
            amount=amount,
            page=page,
            prefix=prefix,
            client=self._client,
        )
        return cast(IndexPage, response.parsed)

    async def create(
        self,
        organization: str,
        *,
        body: CreateIndexRequest,
    ) -> Index:
        """Create an index

         Creates an empty index. Requires the owner or admin role. A new index is usually `ready` in the
        response; if it is still `creating`, read it until it is `ready`. A 409 means the organization
        already has an index with that name, in any case.

        Args:
            organization (str): An account or organization name. Accounts and organizations share one
                namespace. A name keeps the case it was created with, and any spelling that differs only
                in case refers to it; no other account or organization can take such a spelling.
            body (CreateIndexRequest): A new index.

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.

        Returns:
            Index
        """

        response = await create_index.asyncio_detailed(
            organization=organization,
            body=body,
            client=self._client,
        )
        return cast(Index, response.parsed)

    async def get(
        self,
        organization: str,
        index: str,
    ) -> Index:
        """Get an index

         Returns one index with its current state, document count and size, and the progress of its
        background optimization while one runs. Any member can read it.

        Args:
            organization (str): An account or organization name. Accounts and organizations share one
                namespace. A name keeps the case it was created with, and any spelling that differs only
                in case refers to it; no other account or organization can take such a spelling.
            index (str): An index name, unique in its organization. A name keeps the case it was
                created with, and any spelling that differs only in case refers to it; no other index in
                the organization can take such a spelling.

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.

        Returns:
            Index
        """

        response = await get_index.asyncio_detailed(
            organization=organization,
            index=index,
            client=self._client,
        )
        return cast(Index, response.parsed)

    async def update(
        self,
        organization: str,
        index: str,
        *,
        body: UpdateIndexRequest,
    ) -> Index:
        """Update an index

         Changes the index's description or tags. A field absent from the request is left as it is. The name
        is immutable.

        Args:
            organization (str): An account or organization name. Accounts and organizations share one
                namespace. A name keeps the case it was created with, and any spelling that differs only
                in case refers to it; no other account or organization can take such a spelling.
            index (str): An index name, unique in its organization. A name keeps the case it was
                created with, and any spelling that differs only in case refers to it; no other index in
                the organization can take such a spelling.
            body (UpdateIndexRequest): The fields to change. A field that is absent is left as it is;
                at least one must be present.

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.

        Returns:
            Index
        """

        response = await update_index.asyncio_detailed(
            organization=organization,
            index=index,
            body=body,
            client=self._client,
        )
        return cast(Index, response.parsed)

    async def delete(
        self,
        organization: str,
        index: str,
    ) -> None:
        """Delete an index

         Starts deleting an index and all its documents. Requires the owner or admin role. The index is
        `deleting` until the deletion finishes in the background, and it can't be undone.

        Args:
            organization (str): An account or organization name. Accounts and organizations share one
                namespace. A name keeps the case it was created with, and any spelling that differs only
                in case refers to it; no other account or organization can take such a spelling.
            index (str): An index name, unique in its organization. A name keeps the case it was
                created with, and any spelling that differs only in case refers to it; no other index in
                the organization can take such a spelling.

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.

        Returns:
            None
        """

        await delete_index.asyncio_detailed(
            organization=organization,
            index=index,
            client=self._client,
        )


class AsyncDocuments:
    """The documents of an index."""

    def __init__(self, client: Client) -> None:
        self._client = client

    async def list(
        self,
        organization: str,
        index: str,
        *,
        amount: int | Unset = 50,
        page: str | Unset = UNSET,
        prefix: str | Unset = UNSET,
        delimiter: str | Unset = UNSET,
    ) -> DocumentPage:
        """List documents

         Lists documents in key byte order, with each one's revision, size, metadata and whether a search can
        match it. Narrow the listing with `prefix`, and add `delimiter` to browse keys like a directory
        tree: keys that share the part up to the next delimiter are returned once, in `common_prefixes`.

        Args:
            organization (str): An account or organization name. Accounts and organizations share one
                namespace. A name keeps the case it was created with, and any spelling that differs only
                in case refers to it; no other account or organization can take such a spelling.
            index (str): An index name, unique in its organization. A name keeps the case it was
                created with, and any spelling that differs only in case refers to it; no other index in
                the organization can take such a spelling.
            amount (int | Unset):  Default: 50.
            page (str | Unset):
            prefix (str | Unset):
            delimiter (str | Unset):

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.

        Returns:
            DocumentPage
        """

        response = await list_documents.asyncio_detailed(
            organization=organization,
            index=index,
            amount=amount,
            page=page,
            prefix=prefix,
            delimiter=delimiter,
            client=self._client,
        )
        return cast(DocumentPage, response.parsed)

    async def put(
        self,
        organization: str,
        index: str,
        *,
        body: PutDocumentForm,
        idempotency_key: str | Unset = UNSET,
        if_match: str | Unset = UNSET,
        if_none_match: PutDocumentIfNoneMatch | Unset = UNSET,
    ) -> MutationResult:
        """Store one document

         Stores one document of at most 1 GiB. Content that is valid UTF-8 and at most 100 MiB is
        searchable. Any other content, such as an image or a larger file, is stored, listed, and served
        by the document endpoints but is never matched by a search. The `searchable` field of a listing
        reports which applies.

        Args:
            organization (str): An account or organization name. Accounts and organizations share one
                namespace. A name keeps the case it was created with, and any spelling that differs only
                in case refers to it; no other account or organization can take such a spelling.
            index (str): An index name, unique in its organization. A name keeps the case it was
                created with, and any spelling that differs only in case refers to it; no other index in
                the organization can take such a spelling.
            idempotency_key (str | Unset):
            if_match (str | Unset):
            if_none_match (PutDocumentIfNoneMatch | Unset):
            body (PutDocumentForm): One document to store, sent as multipart form fields.

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.

        Returns:
            MutationResult
        """

        response = await put_document.asyncio_detailed(
            organization=organization,
            index=index,
            body=body,
            idempotency_key=idempotency_key,
            if_match=if_match,
            if_none_match=if_none_match,
            client=self._client,
        )
        return cast(MutationResult, response.parsed)

    async def get(
        self,
        organization: str,
        index: str,
        key: str,
        *,
        range_: str | Unset = UNSET,
    ) -> File:
        """Get a document

         Returns a document's content exactly as it was stored, its revision in the ETag header and its
        metadata in the X-Grepvine-Metadata header. Send a Range header to read one byte range; the response
        is then 206, or 416 when the range lies outside the document.

        Args:
            organization (str): An account or organization name. Accounts and organizations share one
                namespace. A name keeps the case it was created with, and any spelling that differs only
                in case refers to it; no other account or organization can take such a spelling.
            index (str): An index name, unique in its organization. A name keeps the case it was
                created with, and any spelling that differs only in case refers to it; no other index in
                the organization can take such a spelling.
            key (str):
            range_ (str | Unset):

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.

        Returns:
            File
        """

        response = await get_document.asyncio_detailed(
            organization=organization,
            index=index,
            key=key,
            range_=range_,
            client=self._client,
        )
        return cast(File, response.parsed)

    async def delete(
        self,
        organization: str,
        index: str,
        key: str,
        *,
        idempotency_key: str | Unset = UNSET,
        if_match: str | Unset = UNSET,
    ) -> MutationResult:
        """Delete one document

         Deletes one document. Send If-Match with a revision to delete it only if it still has that revision.
        Retrying with the same Idempotency-Key returns the original result. Once acknowledged, the document
        no longer matches any search.

        Args:
            organization (str): An account or organization name. Accounts and organizations share one
                namespace. A name keeps the case it was created with, and any spelling that differs only
                in case refers to it; no other account or organization can take such a spelling.
            index (str): An index name, unique in its organization. A name keeps the case it was
                created with, and any spelling that differs only in case refers to it; no other index in
                the organization can take such a spelling.
            key (str):
            idempotency_key (str | Unset):
            if_match (str | Unset):

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.

        Returns:
            MutationResult
        """

        response = await delete_document.asyncio_detailed(
            organization=organization,
            index=index,
            key=key,
            idempotency_key=idempotency_key,
            if_match=if_match,
            client=self._client,
        )
        return cast(MutationResult, response.parsed)

    async def put_batch(
        self,
        organization: str,
        index: str,
        *,
        body: File,
        idempotency_key: str | Unset = UNSET,
    ) -> MutationBatchResult:
        """Store a batch of documents

         Stores up to 2,048 documents. Each document is stored on its own: a document whose precondition
        fails is not stored, the others are, and the result of each document says which happened. Retrying
        with the same Idempotency-Key returns the same results and stores any document an interrupted
        attempt did not reach. Batch content is text carried as JSON strings, so every document stored this
        way is searchable. Store binary content, or a document over 16 MiB, with the
        single-document endpoint. The body may be sent with `Content-Encoding: gzip`; the service decodes it
        before applying the limits below, and answers any other content encoding with 415
        `unsupported_content_encoding`.

        Args:
            organization (str): An account or organization name. Accounts and organizations share one
                namespace. A name keeps the case it was created with, and any spelling that differs only
                in case refers to it; no other account or organization can take such a spelling.
            index (str): An index name, unique in its organization. A name keeps the case it was
                created with, and any spelling that differs only in case refers to it; no other index in
                the organization can take such a spelling.
            idempotency_key (str | Unset):
            body (File): One PutObjectRecord JSON value per line; at most 2,048 records and 16 MiB of
                combined object content.

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.

        Returns:
            MutationBatchResult
        """

        response = await put_objects.asyncio_detailed(
            organization=organization,
            index=index,
            body=body,
            idempotency_key=idempotency_key,
            client=self._client,
        )
        return cast(MutationBatchResult, response.parsed)

    async def delete_batch(
        self,
        organization: str,
        index: str,
        *,
        body: DeleteObjectsRequest,
        idempotency_key: str | Unset = UNSET,
    ) -> MutationBatchResult:
        """Delete a batch of documents

         Deletes up to 2,048 documents. Each document is deleted on its own: a document that does not
        exist or whose precondition fails is not deleted, the others are, and the result of each document
        says which happened. Retrying with the same Idempotency-Key returns the same results.

        Args:
            organization (str): An account or organization name. Accounts and organizations share one
                namespace. A name keeps the case it was created with, and any spelling that differs only
                in case refers to it; no other account or organization can take such a spelling.
            index (str): An index name, unique in its organization. A name keeps the case it was
                created with, and any spelling that differs only in case refers to it; no other index in
                the organization can take such a spelling.
            idempotency_key (str | Unset):
            body (DeleteObjectsRequest): The documents to delete.

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.

        Returns:
            MutationBatchResult
        """

        response = await delete_objects.asyncio_detailed(
            organization=organization,
            index=index,
            body=body,
            idempotency_key=idempotency_key,
            client=self._client,
        )
        return cast(MutationBatchResult, response.parsed)


class AsyncSearch:
    """Search over the documents of an index."""

    def __init__(self, client: Client) -> None:
        self._client = client

    async def query(
        self,
        organization: str,
        index: str,
        *,
        body: QueryRequest,
        amount: int | Unset = 50,
        page: str | Unset = UNSET,
    ) -> QueryPage:
        """Search an index

         Searches every searchable document in the index for a regular expression or literal text, and
        returns each match with the lines it covers, sorted by key, then line, then offset. A metadata
        filter restricts the search to matching documents, and context lines can be returned around each
        result. A pattern or filter that doesn't parse is rejected with 400 and code `invalid_pattern` or
        `invalid_filter`. Continue with `page` while `has_next` is true: a page can be empty while more
        results follow.

        Args:
            organization (str): An account or organization name. Accounts and organizations share one
                namespace. A name keeps the case it was created with, and any spelling that differs only
                in case refers to it; no other account or organization can take such a spelling.
            index (str): An index name, unique in its organization. A name keeps the case it was
                created with, and any spelling that differs only in case refers to it; no other index in
                the organization can take such a spelling.
            amount (int | Unset):  Default: 50.
            page (str | Unset):
            body (QueryRequest): A search: the pattern, how to match it, which documents to search and
                how much context to return.

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.

        Returns:
            QueryPage
        """

        response = await query_index.asyncio_detailed(
            organization=organization,
            index=index,
            body=body,
            amount=amount,
            page=page,
            client=self._client,
        )
        return cast(QueryPage, response.parsed)


class AsyncAPIKeys:
    """The API keys of the signed-in user."""

    def __init__(self, client: Client) -> None:
        self._client = client

    async def list(
        self,
        *,
        amount: int | Unset = 50,
        page: str | Unset = UNSET,
    ) -> APIKeyPage:
        """List API keys

         Lists the authenticated account's API keys, oldest first, including revoked ones. The secret key
        itself is never returned again; `prefix` tells keys apart.

        Args:
            amount (int | Unset):  Default: 50.
            page (str | Unset):

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.

        Returns:
            APIKeyPage
        """

        response = await list_api_keys.asyncio_detailed(
            amount=amount,
            page=page,
            client=self._client,
        )
        return cast(APIKeyPage, response.parsed)

    async def create(
        self,
        *,
        body: CreateAPIKeyRequest,
    ) -> APIKeyCreated:
        """Create an API key

         Creates an API key for the authenticated account. The response is the only time the secret key is
        shown, so store it securely. Send it as a bearer token: `Authorization: Bearer <key>`.

        Args:
            body (CreateAPIKeyRequest): A new API key.

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.

        Returns:
            APIKeyCreated
        """

        response = await create_api_key.asyncio_detailed(
            body=body,
            client=self._client,
        )
        return cast(APIKeyCreated, response.parsed)

    async def revoke(
        self,
        api_key_id: UUID,
    ) -> None:
        """Revoke an API key

         Revokes one of the authenticated account's API keys. Requests authenticated with it are refused from
        then on. A key that doesn't exist or belongs to another account is not found.

        Args:
            api_key_id (UUID):

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.

        Returns:
            None
        """

        await revoke_api_key.asyncio_detailed(
            api_key_id=api_key_id,
            client=self._client,
        )


class AsyncAccount:
    """User accounts: registration, sign-in and the current user."""

    def __init__(self, client: Client) -> None:
        self._client = client

    async def register(
        self,
        *,
        body: RegisterRequest,
    ) -> User:
        """Register a local user

         A 409 has code `username_taken` when an account or an organization already holds the username, and
        code `email_taken` when an account already uses the email address. A 403 has code
        `invitation_required` when registration is by invitation and the request carries none, and code
        `invitation_invalid` when the invitation it carries was already used, was withdrawn or has expired.
        A valid invitation is accepted with the registration, and the account joins the organization it
        names, if any.

        Args:
            body (RegisterRequest): A new local account.

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.

        Returns:
            User
        """

        response = await register_user.asyncio_detailed(
            body=body,
            client=self._client,
        )
        return cast(User, response.parsed)

    async def auth_options(
        self,
    ) -> AuthOptions:
        """Get the sign-in options

         How accounts are created on this service. The console reads it to decide whether to offer
        registration without an invitation.

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.

        Returns:
            AuthOptions
        """

        response = await get_auth_options.asyncio_detailed(
            client=self._client,
        )
        return cast(AuthOptions, response.parsed)

    async def check_invitation(
        self,
        *,
        body: InvitationCheckRequest,
    ) -> InvitationPreview:
        """Check an invitation

         Reports what a pending invitation offers, so the registration form can show it. The token travels in
        the body, never in the URL. An invitation that was used, withdrawn or has expired is not found.

        Args:
            body (InvitationCheckRequest): The invitation to look up.

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.

        Returns:
            InvitationPreview
        """

        response = await check_invitation.asyncio_detailed(
            body=body,
            client=self._client,
        )
        return cast(InvitationPreview, response.parsed)

    async def username_availability(
        self,
        name: str,
    ) -> UsernameAvailability:
        """Check whether a username is available

         Reports whether an account can register this username now. Accounts and organizations share one
        namespace, so a name either one holds, in any case, is taken. The answer can change before the name
        is registered.

        Args:
            name (str): An account or organization name. Accounts and organizations share one
                namespace. A name keeps the case it was created with, and any spelling that differs only
                in case refers to it; no other account or organization can take such a spelling.

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.

        Returns:
            UsernameAvailability
        """

        response = await get_username_availability.asyncio_detailed(
            name=name,
            client=self._client,
        )
        return cast(UsernameAvailability, response.parsed)

    async def login(
        self,
        *,
        body: LoginRequest,
    ) -> User:
        """Create a user session

         Signs in with a username or email address and a password, and starts a browser session: the response
        sets the session cookie and returns, in X-Csrf-Token, the token every state change made with that
        cookie must send. A 401 means the credentials were not accepted. Programs authenticate with an API
        key instead.

        Args:
            body (LoginRequest): Credentials for a new session.

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.

        Returns:
            User
        """

        response = await login.asyncio_detailed(
            body=body,
            client=self._client,
        )
        return cast(User, response.parsed)

    async def logout(
        self,
    ) -> None:
        """Revoke the current session

         Ends the session that made the request and clears its cookie. Other sessions and API keys are
        unaffected.

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.

        Returns:
            None
        """

        await logout.asyncio_detailed(
            client=self._client,
        )

    async def me(
        self,
    ) -> User:
        """Get the current user

         Returns the account the request authenticates as, whether with a session or an API key. A session
        request also receives its CSRF token in X-Csrf-Token.

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.

        Returns:
            User
        """

        response = await get_current_user.asyncio_detailed(
            client=self._client,
        )
        return cast(User, response.parsed)

    async def change_password(
        self,
        *,
        body: ChangePasswordRequest,
    ) -> None:
        """Change the current password

         Changes the signed-in account's password after checking the current one. Every other session of the
        account is signed out; the session that made the request stays signed in, and API keys keep working.
        A 401 means the current password was wrong.

        Args:
            body (ChangePasswordRequest): The current password and its replacement.

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.

        Returns:
            None
        """

        await change_password.asyncio_detailed(
            body=body,
            client=self._client,
        )


class AsyncDeviceLogin:
    """Device login: obtain an API key by approving a code in the browser."""

    def __init__(self, client: Client) -> None:
        self._client = client

    async def start(
        self,
        *,
        body: DeviceAuthorizationRequest,
    ) -> DeviceAuthorization:
        """Start device authorization

         Starts signing in a device, such as the command-line client, without entering a password on it. Show
        the user `user_code` and send them to `verification_uri` (or `verification_uri_complete`) to approve
        it in a signed-in browser, then poll for the API key with `device_code`. The authorization expires
        after `expires_in` seconds.

        Args:
            body (DeviceAuthorizationRequest): A request to sign in a device.

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.

        Returns:
            DeviceAuthorization
        """

        response = await start_device_authorization.asyncio_detailed(
            body=body,
            client=self._client,
        )
        return cast(DeviceAuthorization, response.parsed)

    async def approve(
        self,
        *,
        body: DeviceDecisionRequest,
    ) -> None:
        """Approve device authorization

         Approves a pending device authorization for the signed-in account, identified by the code the device
        shows. The device's next poll receives a new API key with the name it asked for. A code that is
        unknown, already decided or expired is not found.

        Args:
            body (DeviceDecisionRequest): The device authorization to approve or deny.

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.

        Returns:
            None
        """

        await approve_device_authorization.asyncio_detailed(
            body=body,
            client=self._client,
        )

    async def deny(
        self,
        *,
        body: DeviceDecisionRequest,
    ) -> None:
        """Deny device authorization

         Denies a pending device authorization, identified by the code the device shows. The device's next
        poll fails with code `access_denied`. A code that is unknown, already decided or expired is not
        found.

        Args:
            body (DeviceDecisionRequest): The device authorization to approve or deny.

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.

        Returns:
            None
        """

        await deny_device_authorization.asyncio_detailed(
            body=body,
            client=self._client,
        )

    async def poll(
        self,
        *,
        body: DeviceTokenRequest,
    ) -> APIKeyCreated:
        """Poll for a device API key

         Exchanges an approved device code for an API key, once. Until the user decides, a poll fails with
        400 and code `authorization_pending`: poll again after `interval` seconds. Polling sooner fails with
        `slow_down` and adds 5 seconds to the interval. A denied authorization fails with `access_denied`,
        and an unknown, expired or already used code with `expired_token`.

        Args:
            body (DeviceTokenRequest): The device code to exchange for an API key.

        Raises:
            grepvine.APIError: The service answered with an error.
            grepvine.TransportError: The request could not be delivered.

        Returns:
            APIKeyCreated
        """

        response = await poll_device_token.asyncio_detailed(
            body=body,
            client=self._client,
        )
        return cast(APIKeyCreated, response.parsed)


class _GeneratedAsyncClient:
    """The API's resources."""

    organizations: AsyncOrganizations
    indexes: AsyncIndexes
    documents: AsyncDocuments
    search: AsyncSearch
    api_keys: AsyncAPIKeys
    account: AsyncAccount
    device_login: AsyncDeviceLogin

    def __init__(self, client: Client) -> None:
        self._client = client
        self.organizations = AsyncOrganizations(client)
        self.indexes = AsyncIndexes(client)
        self.documents = AsyncDocuments(client)
        self.search = AsyncSearch(client)
        self.api_keys = AsyncAPIKeys(client)
        self.account = AsyncAccount(client)
        self.device_login = AsyncDeviceLogin(client)
