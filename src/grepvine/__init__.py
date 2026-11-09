"""Python SDK for the Grepvine search API."""

from importlib.metadata import version

from grepvine import models
from grepvine._client import *
from grepvine._config import Settings
from grepvine._generated.api.resources import (
    Account,
    APIKeys,
    AsyncAccount,
    AsyncAPIKeys,
    AsyncIndexCreation,
    AsyncIndexDeletion,
    AsyncMembers,
    AsyncOrganizations,
    AsyncSearch,
    IndexCreation,
    IndexDeletion,
    Members,
    Organizations,
    Search,
)
from grepvine._helpers import *
from grepvine._index import *
from grepvine._retry import RetryPolicy
from grepvine.errors import *

__version__ = version("grepvine")
__all__ = [
    "__version__",
    "models",
    "paginate",
    "index",
    "default_client",
    "set_default_client",
    "Client",
    "AsyncClient",
    "IndexClient",
    "AsyncIndexClient",
    "IndexCreation",
    "AsyncIndexCreation",
    "IndexDeletion",
    "AsyncIndexDeletion",
    "Prefix",
    "RetryPolicy",
    "Settings",
    "Organizations",
    "AsyncOrganizations",
    "Members",
    "AsyncMembers",
    "Indexes",
    "AsyncIndexes",
    "Documents",
    "AsyncDocuments",
    "DocumentInput",
    "MetadataValue",
    "Search",
    "AsyncSearch",
    "APIKeys",
    "AsyncAPIKeys",
    "Account",
    "AsyncAccount",
    "DeviceLogin",
    "AsyncDeviceLogin",
    "GrepvineError",
    "APIError",
    "InvalidRequestError",
    "InvalidPageError",
    "AuthenticationError",
    "PermissionDeniedError",
    "NotFoundError",
    "ConflictError",
    "PreconditionFailedError",
    "PayloadTooLargeError",
    "RangeNotSatisfiableError",
    "RateLimitedError",
    "ServerError",
    "ConfigurationError",
    "TransportError",
    "PartialBatchError",
    "WaitError",
    "WaitTimeoutError",
    "OperationFailedError",
]
