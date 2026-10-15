"""Python SDK for the Grepvine search API."""

from __future__ import annotations

from grepvine_sdk._async.client import AsyncClient
from grepvine_sdk._async.paginator import AsyncPaginator
from grepvine_sdk._async.resources import (
    AsyncAccount,
    AsyncAPIKeys,
    AsyncDeviceLogin,
    AsyncDocuments,
    AsyncIndex,
    AsyncIndexes,
    AsyncMembers,
    AsyncOrganizations,
)
from grepvine_sdk._core.retry import RetryPolicy
from grepvine_sdk._http import ClientConfig
from grepvine_sdk._sync.client import Client
from grepvine_sdk._sync.paginator import Paginator
from grepvine_sdk._sync.resources import (
    Account,
    APIKeys,
    DeviceLogin,
    Documents,
    Index,
    Indexes,
    Members,
    Organizations,
)
from grepvine_sdk._version import __version__
from grepvine_sdk.errors import (
    APIError,
    AuthenticationError,
    ConfigurationError,
    ConflictError,
    GrepvineError,
    InvalidPageError,
    InvalidRequestError,
    NotFoundError,
    PartialBatchError,
    PayloadTooLargeError,
    PermissionDeniedError,
    PreconditionFailedError,
    RangeNotSatisfiableError,
    RateLimitedError,
    ServerError,
    TransportError,
)
from grepvine_sdk.models import (
    APIKey,
    APIKeyCreated,
    ContentRange,
    ContextLine,
    DeviceAuthorization,
    Document,
    DocumentError,
    DocumentSummary,
    IndexData,
    Match,
    Member,
    MutationResult,
    Organization,
    Page,
    SearchResult,
    Span,
    User,
)

default_client: Client = Client()
"""The client behind :data:`organizations` and :data:`indexes`; change it with :func:`configure`."""

organizations: Organizations = default_client.organizations
indexes: Indexes = default_client.indexes
configure = default_client.configure

__all__ = [
    "APIError",
    "APIKey",
    "APIKeyCreated",
    "APIKeys",
    "Account",
    "AsyncAPIKeys",
    "AsyncAccount",
    "AsyncClient",
    "AsyncDeviceLogin",
    "AsyncDocuments",
    "AsyncIndex",
    "AsyncIndexes",
    "AsyncMembers",
    "AsyncOrganizations",
    "AsyncPaginator",
    "AuthenticationError",
    "Client",
    "ClientConfig",
    "ConfigurationError",
    "ConflictError",
    "ContentRange",
    "ContextLine",
    "DeviceAuthorization",
    "DeviceLogin",
    "Document",
    "DocumentError",
    "DocumentSummary",
    "Documents",
    "GrepvineError",
    "Index",
    "IndexData",
    "Indexes",
    "InvalidPageError",
    "InvalidRequestError",
    "Match",
    "Member",
    "Members",
    "MutationResult",
    "NotFoundError",
    "Organization",
    "Organizations",
    "Page",
    "Paginator",
    "PartialBatchError",
    "PayloadTooLargeError",
    "PermissionDeniedError",
    "PreconditionFailedError",
    "RangeNotSatisfiableError",
    "RateLimitedError",
    "RetryPolicy",
    "SearchResult",
    "ServerError",
    "Span",
    "TransportError",
    "User",
    "__version__",
    "configure",
    "default_client",
    "indexes",
    "organizations",
]
