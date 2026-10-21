# Grepvine Python SDK

The Python SDK for Grepvine, a search service for large collections of text:
regular-expression and literal search over every line of every document, with
metadata filters and paged results. It covers the whole Grepvine API:
organizations and their members, indexes, documents, search, API keys, user
accounts and device login.

## Installation

```sh
pip install grepvine
# or
uv add grepvine
```

Python 3.11 or later. The package is imported as `grepvine`, ships type
hints, and has both a synchronous and an asynchronous client.

## Authentication

Pass your API key, and the endpoint when you use a service other than
`https://api.grepvine.ai`:

```python
import grepvine

client = grepvine.Client(api_key="gvk_...", endpoint="https://grepvine.example.com")
```

The SDK reads no environment variables or configuration files; pass the values
from wherever your application keeps them. An endpoint may be given with or
without `/v1`. A `Client` also takes `timeout` (seconds, or an
`httpx.Timeout`), `retry` (a `RetryPolicy`, see [Errors](#errors)) and
`transport` (an `httpx` transport, such as `httpx.MockTransport` in tests).
Use it as a context manager, or call `close()`, to release its connections.
To obtain a key without a browser session, see [Device login](#device-login).

The client's resources follow the API: `client.organizations` (with
`client.organizations.members`), `client.indexes`, `client.documents`,
`client.search`, `client.api_keys`, `client.account` and
`client.device_login`. Each method takes the operation's path parameters
(`organization`, `index`, `key`) positionally, and its query parameters and
request body (`body=`, a model from `grepvine.models`) by name. It returns
the API's response model, or `None` for an empty answer.

## Organizations

```python
from grepvine.models import (
    AddMemberRequest,
    AddMemberRequestRole,
    CreateOrganizationRequest,
    TransferOwnershipRequest,
    UpdateMemberRequest,
    UpdateMemberRequestRole,
)

for org in grepvine.paginate(client.organizations.list):
    print(org.name, org.role)

org = client.organizations.get("my-org")
client.organizations.create(body=CreateOrganizationRequest(name="my-org"))  # you become its owner

members = client.organizations.members
members.add("my-org", body=AddMemberRequest(user="bob", role=AddMemberRequestRole.DEVELOPER))
members.update("my-org", "bob", body=UpdateMemberRequest(role=UpdateMemberRequestRole.ADMIN))
for member in grepvine.paginate(members.list, organization="my-org"):
    print(member.user.name, member.role)
members.remove("my-org", "bob")

# The old owner becomes an admin.
client.organizations.transfer_ownership("my-org", body=TransferOwnershipRequest(user="carol"))
client.organizations.delete("my-org")  # deletion completes in the background
```

Organizations and user accounts share one namespace, so an organization name
must not be taken by a user either. Adding, changing and removing members
needs the admin or owner role; transferring ownership and deleting the
organization need the owner role.

## Indexes

```python
from grepvine.models import CreateIndexRequest, IndexTagChanges, IndexTags, UpdateIndexRequest

client.indexes.create(
    "my-org",
    body=CreateIndexRequest(
        name="my-index",
        description="# Product docs\n\nEvery guide we publish.",  # Markdown, optional
        tags=IndexTags.from_dict({"team": "search", "commit": "3f9c2a1"}),  # optional
    ),
)
index = client.indexes.wait_until_ready("my-org", "my-index", timeout=60)
print(index.state, index.document_count, index.tags["commit"])

for summary in grepvine.paginate(client.indexes.list, organization="my-org", prefix="docs-"):
    print(f"{summary.name}: {summary.document_count} documents")

# Set one tag and remove another; tags left out stay as they are.
changes = IndexTagChanges.from_dict({"team": "platform", "commit": None})
client.indexes.update("my-org", "my-index", body=UpdateIndexRequest(tags=changes))
client.indexes.delete("my-org", "my-index")  # deletion completes in the background
```

A new index is `creating` for a moment before it is `ready`.
`indexes.wait_until_ready(organization, index, timeout=..., interval=...)`
reads the index until it is ready and returns it. It raises `TimeoutError`
after `timeout` seconds (300 by default), and `GrepvineError` for an index
that is being deleted.

An index's `description` is Markdown, at most 16,384 characters, and empty
when none was set. `update` sends only the fields you set, so changing the
description leaves the tags alone and the other way round. Changing a
description or tags needs the admin or owner role.

## Search

```python
from grepvine.models import QueryRequest, QueryRequestMode

query = QueryRequest(
    pattern="hello world",
    mode=QueryRequestMode.LITERAL,  # the default is a regular expression
    case_sensitive=False,
    whole_word=True,  # literal mode only
    filter_="path STARTSWITH 'src/' AND size < 100000",
    lines_before=2,
    lines_after=2,
)
for result in grepvine.paginate(
    client.search.query, organization="my-org", index="my-index", body=query
):
    print(f"{result.key}:{result.line_number}: {result.text}")
```

`client.search.query` returns one `QueryPage`; `grepvine.paginate` walks
every page. A result carries the covered `text`, its `line_number`, the
context lines, and the `matches` as byte offsets within the document.

Filters are expressions over document metadata, such as
`path STARTSWITH 'docs/' AND mtime >= (CURRENT_DATE - INTERVAL '3 days')`.
`documents.put_many` records `path` and `size` metadata on every document it
stores, so filters on those fields work without extra effort.

## Documents

```python
results = client.documents.put_many(
    "my-org",
    "my-index",
    [
        {"key": "a.txt", "content": "alpha", "metadata": {"lang": "en"}},
        {"key": "b.txt", "content": b"beta", "if_none_match": True},
        {"key": "c.txt", "content": "gamma", "if_match": revision},
    ],
)
for result in results:
    if result.error:
        print(f"{result.key} was not stored: {result.error.error}")

for document in grepvine.paginate(
    client.documents.list, organization="my-org", index="my-index", prefix="notes/"
):
    print(document.key, document.content_bytes, document.searchable)

file = client.documents.get("my-org", "my-index", "a.txt")
print(file.payload.read())

client.documents.delete("my-org", "my-index", "a.txt")
```

`put_many` stores text documents in as few requests as possible, at most
2,048 documents and 16 MiB of text per request, and returns one
`MutationResult` per document in input order. Content is a `str` or UTF-8
`bytes`. Metadata values may be `str`, `int`, `float`, `bool`, or `datetime`;
the SDK tags them for the API, and adds `path` (the key) and `size` fields,
which your own fields override. A document may carry up to 64 metadata
fields.

A document whose `if_match` or `if_none_match` condition fails is left
unchanged and the others are written; its result has no `revision`, and its
`error` has the `code` `"precondition_failed"`. If a request fails after
earlier requests were answered, `put_many` raises `PartialBatchError` with
`committed` (the results so far), `failed_keys` (the documents of the failed
request; the service may have written some of them) and `pending_keys` (the
documents never sent). If the first request fails, the SDK raises its error
unchanged. To finish an interrupted call safely, pass an `idempotency_key` of
at least 16 characters and repeat the call with the same key and the same
documents: no document is written twice.

For a binary document, or one larger than 16 MiB, use `documents.put` with a
`PutDocumentForm`. Documents can be up to 1 GiB; content that is valid UTF-8
and at most 100 MiB is searchable, and anything else is stored and served but
never matched by a search. `documents.put_batch` and `documents.delete_batch`
send one request each, and `documents.delete` removes one document; with
`if_match`, a failed condition on `put` or `delete` raises
`PreconditionFailedError`.

## Pagination

Every list method, and `search.query`, returns one page: its `results` and a
`pagination` with `next_page_id` and `has_next`. `grepvine.paginate` takes
the method and its arguments by name and yields every result, following
`next_page_id` while `has_next` is true:

```python
for index in grepvine.paginate(client.indexes.list, organization="acme"):
    print(index.name)

page = client.indexes.list("acme", amount=100)  # one page of up to 100
later = client.indexes.list("acme", amount=100, page=page.pagination.next_page_id)
```

A page may be empty while more results follow, especially in search;
`paginate` keeps going until the service reports the end. A `next_page_id` is
valid for 15 minutes and only with the same arguments, including `amount`;
otherwise the service answers with `InvalidPageError`. With `AsyncClient`,
iterate with `async for`.

## Errors

Every error is a `GrepvineError`. Errors from the service are `APIError`
subclasses with `status_code`, `code`, `reason`, `message`, `request_id` and,
when the service sent one, `retry_after`:

| Exception | When |
|---|---|
| `InvalidRequestError` | The request was rejected; fix the input. `InvalidPageError` for a bad page token. |
| `AuthenticationError` | The API key is missing or not valid. |
| `PermissionDeniedError` | The key may not perform the action. |
| `NotFoundError` | The resource does not exist or is not visible. |
| `ConflictError` | The request conflicts with the current state, such as creating an index that exists. |
| `PreconditionFailedError` | An `if_match` or `if_none_match` condition failed on a single-document write. |
| `PayloadTooLargeError` | A document or batch is over its size limit. |
| `RangeNotSatisfiableError` | A byte range does not overlap the document. |
| `RateLimitedError` | The service kept asking the client to slow down for longer than the client was willing to wait. |
| `ServerError` | The service failed on every attempt. |

`ConfigurationError` means the endpoint is not an `http` or `https` URL.
`TransportError` means the request could not be delivered. `PartialBatchError`
is described under [Documents](#documents).

The SDK retries on its own. A `429` waits for the interval the service asks
for in `Retry-After` (with jitter, up to a minute at a time and ten minutes in
total per request). A `5xx` answer or a connection failure is retried twice
more with a short backoff. Every write carries an `Idempotency-Key` that
stays the same across retries, so a retried write is applied once. Pass
`retry=grepvine.RetryPolicy(...)` to change these bounds.

## Asynchronous use

`AsyncClient` takes the same arguments and has the same resources and
methods, awaited. Create it inside the event loop that will use it:

```python
import asyncio

import grepvine
from grepvine.models import QueryRequest


async def main() -> None:
    async with grepvine.AsyncClient(api_key="gvk_...") as client:
        await client.indexes.wait_until_ready("my-org", "my-index")
        await client.documents.put_many("my-org", "my-index", [{"key": "a.txt", "content": "alpha"}])
        query = QueryRequest(pattern="alpha")
        async for result in grepvine.paginate(
            client.search.query, organization="my-org", index="my-index", body=query
        ):
            print(result.key, result.line_number)


asyncio.run(main())
```

## API keys

A signed-in user manages their API keys through `client.api_keys`:

```python
from grepvine.models import CreateAPIKeyRequest

key = client.api_keys.create(body=CreateAPIKeyRequest(name="ci"))  # 1 to 128 characters
print(key.key)  # the secret, shown only now

for listed in grepvine.paginate(client.api_keys.list):
    print(listed.id, listed.name, listed.prefix, listed.last_used_at, listed.revoked_at)

client.api_keys.revoke(key.id)
```

A listing shows each key's `prefix`, never its secret. A revoked key stays in
the listing with its `revoked_at` time, and requests that use it fail with
`AuthenticationError`.

## Account

`client.account` registers users, signs them in and out, and changes their
password. The API key is the way to authenticate everything else; a session is
for scripts that start from a username and password, such as end-to-end tests
that create an account and its first API key. Create the client without an
API key for them:

```python
from grepvine.models import ChangePasswordRequest, LoginRequest, RegisterRequest

client = grepvine.Client(endpoint="https://grepvine.example.com")

if client.account.username_availability("alice").available:
    client.account.register(
        body=RegisterRequest(name="alice", email="alice@example.com", password="a long passphrase")
    )
client.account.login(body=LoginRequest(identifier="alice", password="a long passphrase"))

print(client.account.me().email)
client.account.change_password(
    body=ChangePasswordRequest(current_password="a long passphrase", new_password="a longer one!")
)
client.account.logout()
```

`login` starts a session on the client: later requests carry its cookie and
CSRF token. A taken username or email address raises `ConflictError` with
code `"username_taken"` or `"email_taken"`, and wrong credentials raise
`AuthenticationError`. Passwords are at least 12 characters.

## Device login

Device login gives an API key to a program, such as a command-line tool or an
agent, once a person approves it in a signed-in browser. `authorize` does the
program's part in one call: it starts the login, hands the code to `on_code`
to show, and waits for the person's decision, polling at the interval the
service asks for and slowing down when asked to.

```python
from grepvine.models import DeviceAuthorization


def show(authorization: DeviceAuthorization) -> None:
    print(f"Open {authorization.verification_uri_complete}")
    print(f"and check that it shows {authorization.user_code}")


with grepvine.Client() as anonymous:  # starting a device login needs no API key
    key = anonymous.device_login.authorize("my laptop", on_code=show, timeout=600)
client = grepvine.Client(api_key=key.key)
```

A denied login raises `InvalidRequestError` with code `"access_denied"`, and
an expired one with `"expired_token"`. A login that is not approved within
`timeout` seconds, or before it expires, raises `TimeoutError`.

The steps are also available one at a time: the program calls
`device_login.start` and `device_login.poll`, and the person, or a tool
acting for them, calls `device_login.approve` or `device_login.deny` with the
user code. `poll` raises `InvalidRequestError` with code
`"authorization_pending"` while the person has not decided, and `"slow_down"`
when polled more often than the authorization's `interval`.

## Other requests

`client.http` is the `httpx.Client` (an `httpx.AsyncClient` for
`AsyncClient`) the client sends its requests with: it has the endpoint,
credentials, timeout and retries, and raises the SDK's errors. Use it for
anything the methods above do not cover, such as streaming a large document
to a file:

```python
from urllib.parse import quote

path = f"/organizations/my-org/indexes/my-index/objects/{quote('videos/demo.mp4', safe='')}"
with client.http.stream("GET", path) as response, open("demo.mp4", "wb") as file:
    for chunk in response.iter_bytes():
        file.write(chunk)
```

Paths are relative to the endpoint's `/v1`.

## Thread safety

A `Client` may be shared between threads. An iterator from `paginate` is not
thread-safe.

## Limits worth knowing

- One document: at most 1 GiB, and a single upload must finish within the
  service's request deadline of 35 seconds.
- One batch: at most 2,048 documents and 16 MiB of text.
- Keys: 1 to 1,024 characters. Organization and index names: letters, digits,
  and hyphens, starting with a letter. A name keeps the case it was created
  with, and any spelling that differs only in case refers to the same
  organization or index.
- `lines_before` and `lines_after`: at most 20 each.
- Tags: at most 64 per index. A key is 1 to 128 characters without whitespace
  or control characters; a value is at most 1,024 characters without control
  characters.

## Examples

The `examples` directory holds complete programs. They read the API key from
`GREPVINE_API_KEY` and, for a service other than the default, the endpoint from
`GREPVINE_API_ENDPOINT`, and pass them to the client:

```sh
export GREPVINE_ORGANIZATION=my-org
python examples/ingest_search.py        # add --keep-index to keep the documents
python examples/ingest_search_async.py
python examples/device_login.py
```

The ingest example creates a uniquely named index, stores three documents,
searches them with and without a metadata filter, and deletes the index at
the end. The organization must exist, and the key needs permission to create
and delete indexes.

## License

Licensed under the Apache License 2.0. See `LICENSE` and `NOTICE`.
