# Grepvine Python SDK

The Python SDK for Grepvine, a search service for large collections of text:
regular-expression and literal search over every line of every document, with
metadata filters and paged results. It covers the whole Grepvine API:
organizations and their members, indexes, documents, search, API keys, user
accounts and device login.

```python
import grepvine

index = grepvine.index("acme/support")  # configured like gv; see Configuration
for hit in index.search(pattern=r"(TODO|FIXME)\b", filter="path STARTSWITH 'src/'"):
    print(f"{hit.key}:{hit.line_number}: {hit.text}")
```

## Installation

```sh
pip install grepvine
# or
uv add grepvine
```

Python 3.11 or later. The package is imported as `grepvine`, ships type
hints, and has both a synchronous and an asynchronous client.

## Configuration

A client finds its settings the way `gv` does, so after `gv login` the SDK
needs no setup. Each setting comes from the first of:

1. the argument to `grepvine.Client(...)`;
2. its environment variable;
3. the configuration file: `$GREPVINE_CONFIG`, else `~/.grepvine/config.yaml`
   when it exists;
4. its default.

| Argument | Environment variable | Default |
|---|---|---|
| `api_key` | `GREPVINE_API_KEY` | None. |
| `endpoint` | `GREPVINE_API_ENDPOINT` | `https://api.grepvine.ai` |
| `organization` | `GREPVINE_ORGANIZATION` | None. |

```python
import os

import grepvine

client = grepvine.Client()                                       # configured like gv
client = grepvine.Client(api_key=os.environ["CI_GREPVINE_KEY"])  # one setting overridden
from_env = grepvine.Client.from_env()                            # environment variables only
staging = grepvine.Client.from_config("~/.grepvine/staging.yaml")  # one file only
isolated = grepvine.Client(api_key="gvk_...", trust_env=False)   # arguments only
```

`Client.from_env()` takes its settings only from the three environment
variables, and `Client.from_config(path)` only from that file; a setting either
leaves out takes its default. `trust_env=False` makes a client whose settings
come only from its arguments. `AsyncClient` has the same forms, and all of them
take `timeout`, `retry` and `transport`.

### Proxies and certificates

Like curl, pip and httpx, a client sends its requests through the proxy that
`HTTPS_PROXY` (or `HTTP_PROXY`, or `ALL_PROXY`) names, connects directly to the
hosts that `NO_PROXY` lists, and trusts the certificate authorities in
`SSL_CERT_FILE` or `SSL_CERT_DIR`. These variables apply to every client,
including one made with `trust_env=False`, which concerns only the Grepvine
settings. A `socks5://` proxy needs `pip install "httpx[socks]"`. Through a
proxy, an `https` endpoint is reached through a tunnel, so the proxy sees the
host name but not the API key or the content.

To choose a proxy in code, or to connect directly whatever the variables say,
pass an httpx transport. The client still retries requests through it:

```python
import httpx

proxied = grepvine.Client(transport=httpx.HTTPTransport(proxy="http://proxy.internal:3128"))
direct = grepvine.Client(transport=httpx.HTTPTransport())
```

Clients configured differently can be used side by side. The configuration
file is refused if other users can read it, as `gv` refuses it. An endpoint
may be given with or without `/v1`. `client.settings` shows what a client
uses.

`grepvine.index(...)` and the other module-level functions use a default
client, `Client()`, created on first use. `grepvine.set_default_client(client)`
replaces it.

A `Client` also takes `timeout` (seconds, or an `httpx.Timeout`), `retry` (a
`RetryPolicy`, see [Errors](#errors)) and `transport` (an `httpx` transport,
such as `httpx.MockTransport` in tests). Use it as a context manager, or call
`close()`, to release its connections. To obtain a key without a browser
session, see [Device login](#device-login).

## Indexes

`client.index(name)` is an `IndexClient`: one index, named as
`organization/index`, or by its name alone in the default organization. Making
one sends no request; its methods do.

```python
index = client.index("acme/support")

index.create(
    description="# Support tickets\n\nOne Markdown file per ticket.",  # Markdown, optional
    tags={"team": "support"},  # optional
).wait(timeout=60)

info = index.info()
print(info.state, info.document_count, info.tags["team"])

# Set one tag and remove another; tags left out stay as they are.
index.update(tags={"team": "platform", "commit": None})
index.delete_index().wait()
```

Creating and deleting an index finish in the background, so `create` returns
an `IndexCreation` and `delete_index` an `IndexDeletion`. Their `result` is the
service's answer: for a creation, the index in its `creating` state. `wait()`
reads the index until the work is done: a creation returns the ready index, and
a deletion returns once the index is gone and its name can be used again.

`wait(timeout)` takes seconds, 300 by default; `wait(None)` waits without a
limit. A wait that ends before the work is done raises a `WaitError`, with
`target` (such as `"index acme/support"`) and the last `state` seen:

```python
creation = index.create()
try:
    creation.wait(timeout=30)
except grepvine.WaitTimeoutError:
    ...  # not ready yet; the index is still being created, so wait again later
except grepvine.OperationFailedError as error:
    print(f"{error.target} is {error.state}")  # it will not become ready by itself
```

`WaitTimeoutError` is also a built-in `TimeoutError`. `except grepvine.WaitError`
catches both, and `except grepvine.GrepvineError` also catches a failed request
while waiting.

`index.wait_until_ready()` waits for an index that was created elsewhere, such
as by another process.

An index's `description` is Markdown, at most 16,384 characters, and empty
when none was set. `update` sends only the arguments you pass, so changing the
description leaves the tags alone and the other way round. Changing a
description or tags needs the admin or owner role.

To list the indexes of an organization:

```python
for summary in client.indexes.list("acme", prefix="docs-"):
    print(f"{summary.name}: {summary.document_count} documents")
```

## Search

```python
for hit in index.search(
    pattern="connection reset by peer",
    mode="literal",  # the default is "regex"
    case_sensitive=False,
    whole_word=True,  # literal mode only
    filter="path STARTSWITH 'src/' AND size < 100000",
    lines_before=2,
    lines_after=2,
):
    print(f"{hit.key}:{hit.line_number}: {hit.text}")
```

`search` returns an iterator over every result on every page, as `gv search`
prints them; it sends a
request when the iteration reaches a page, so stopping early sends no more.
A result carries the covered `text`, its `line_number`, the context lines, and
the `matches` as byte offsets within the document. An option left out, or
passed as `None`, takes the service's default.

Filters are expressions over document metadata, such as
`path STARTSWITH 'docs/' AND mtime >= (CURRENT_DATE - INTERVAL '3 days')`.
`put_many` records `path` and `size` metadata on every document it stores, so
filters on those fields work without extra effort.

## Documents

```python
from datetime import UTC, datetime
from pathlib import Path

results = index.put_many(
    [
        {"key": "a.txt", "content": "alpha", "metadata": {"lang": "en"}},
        {"key": "b.txt", "content": b"beta", "if_none_match": True},
        {"key": "c.txt", "content": "gamma", "if_match": revision},
    ],
    idempotency_key="import-2026-10-14",
)
for result in results:
    if result.error:
        print(f"{result.key} was not stored: {result.error.error}")

index.put("report.pdf", Path("out/report.pdf"), metadata={"pages": 12, "reviewed": datetime.now(UTC)})

for entry in index.list(prefix="notes/"):
    print(entry.key, entry.content_bytes, entry.searchable)

file = index.get("a.txt", range="bytes=0-99")
print(file.payload.read())

index.delete("a.txt")
index.delete_batch(objects=[{"key": "b.txt"}, {"key": "c.txt"}])
```

`put_many` stores text documents in as few requests as possible, at most
2,048 documents and 16 MiB of text per request, and returns one
`MutationResult` per document in input order. Content is a `str` or UTF-8
`bytes`; binary content goes through `put`. `documents` may be a list or any
iterable, such as a generator: it is read one batch at a time, so about 16 MiB
of content is held in memory however many documents there are. It adds `path`
(the key) and `size` metadata fields, which your own fields override. A
document may carry up to 64 metadata fields.

`put` stores one document of up to 1 GiB, text or binary. Content that is
valid UTF-8 and at most 100 MiB is searchable; anything else is stored and
served but never matched by a search. `content` is any of:

| `content` | Sent |
|---|---|
| `str` or `bytes` | as is; a `str` is always content, never a path |
| a `pathlib.Path` | the file at that path, streamed |
| a binary file object, such as `open(path, "rb")` or `io.BytesIO` | streamed from where it is |
| an iterable of `bytes`, such as a generator | streamed as it is produced |
| an async iterable of `bytes` (`AsyncIndexClient` only) | streamed as it is produced |

```python
import json
import urllib.request


def rows(records):  # content made by your program, never held in memory whole
    for record in records:
        yield (json.dumps(record) + "\n").encode()


index.put("exports/records.ndjson", rows({"n": n} for n in range(100_000)))

with urllib.request.urlopen("https://example.com/data.csv") as response:  # length known
    index.put("mirror/data.csv", response, size=int(response.headers["Content-Length"]))
```

Pass `size`, the content's length in bytes, when you stream content whose
length you know: without it, an upload must finish within 35 seconds; with it,
the service allows longer in proportion to the size. Content of another length
raises `ValueError`.

Content in memory, paths and files that can seek are sent again when an attempt
fails and is retried. Content read from a stream (chunks, or a file that cannot
seek, such as a pipe) is sent once: a failed attempt raises its error, such as
`ServerError` or `TransportError`, and the content must be given to `put`
again.
`if_match` stores it only over that revision, and `if_none_match=True` only
when the key is new; a failed condition raises `PreconditionFailedError`, as
it does for `delete` with `if_match`.

In `put` and `put_many`, metadata values are `str`, `int`, `float`, `bool` or
`datetime`. Listings return every value tagged, as a
`TaggedStringMetadataValue`, `TaggedIntegerMetadataValue`,
`TaggedNumberMetadataValue`, `TaggedBooleanMetadataValue` or
`TaggedTimestampMetadataValue`, whose `value` holds the `str`, `int`, `float`,
`bool` or `datetime`:

```python
[entry] = index.list(prefix="report")
print(entry.metadata["pages"].value)  # 12
```

With a `delimiter`, `list` folds the keys that share the text up to the next
delimiter into one `grepvine.Prefix`, like a folder, and yields each page's
prefixes before its documents:

```python
for entry in index.list(prefix="tickets/", delimiter="/"):
    print(entry.prefix if isinstance(entry, grepvine.Prefix) else entry.key)
```

In `put_many`, a document whose `if_match` or `if_none_match` condition fails
is left unchanged and the others are written; its result has no `revision`,
and its `error` has the `code` `"precondition_failed"`. If a request fails
after earlier requests were answered, `put_many` raises `PartialBatchError`
with `committed` (the results so far), `failed_keys` (the documents of the
failed request; the service may have written some of them) and `pending_keys`
(the documents never sent). If the first request fails, the SDK raises its
error unchanged. To finish an interrupted call safely, pass an
`idempotency_key` of at least 16 characters and repeat the call with the same
key and the same documents: no document is written twice.

## Pagination

Every listing, and `search`, has two forms. The plain method, such as
`index.search(...)` or `client.organizations.list()`, is an iterator over every
result, following `next_page_id` while `has_next` is true. The `_page` form,
such as `index.search_page(...)`, returns one page: its `results` and a
`pagination` with `next_page_id` and `has_next`.

```python
page = client.indexes.list_page("acme", amount=100)  # one page of up to 100
later = client.indexes.list_page("acme", amount=100, page=page.pagination.next_page_id)
```

A page may be empty while more results follow, especially in search; the
iterators keep going until the service reports the end. A `next_page_id` is
valid for 15 minutes and only with the same arguments, including `amount`;
otherwise the service answers with `InvalidPageError`.
`grepvine.paginate(method, **arguments)` iterates over a `_page` method's
results the same way.

## Errors

Every error is a `GrepvineError`. Errors from the service are `APIError`
subclasses with `status_code`, `code`, `reason`, `message`, `request_id` and,
when the service sent one, `retry_after`:

| Exception | When |
|---|---|
| `InvalidRequestError` | The request was rejected; fix the input. `InvalidPageError` for a bad page token. |
| `AuthenticationError` | The API key is missing or not valid. |
| `PermissionDeniedError` | The key may not perform the action. Code `"organization_suspended"` when the organization is suspended. |
| `NotFoundError` | The resource does not exist or is not visible. |
| `ConflictError` | The request conflicts with the current state, such as creating an index that exists. |
| `PreconditionFailedError` | An `if_match` or `if_none_match` condition failed on a single-document write. |
| `PayloadTooLargeError` | A document or batch is over its size limit. |
| `RangeNotSatisfiableError` | A byte range does not overlap the document. |
| `RateLimitedError` | The service kept asking the client to slow down for longer than the client was willing to wait. |
| `ServerError` | The service failed on every attempt. |

`WaitError` (`WaitTimeoutError` or `OperationFailedError`) is described under
[Indexes](#indexes). `ConfigurationError` means a setting is not usable: the endpoint is not an
`http` or `https` URL, the configuration file is missing, unreadable or
readable by other users, or an index is named without an organization and
there is no default one. `TransportError` means the request could not be
delivered. `PartialBatchError` is described under [Documents](#documents).

```python
try:
    index.create()
except grepvine.ConflictError:
    pass  # it exists already
```

The SDK retries on its own. A `429` waits for the interval the service asks
for in `Retry-After` (with jitter, up to a minute at a time and ten minutes in
total per request). A `5xx` answer or a connection failure is retried twice
more with a short backoff. Every write carries an `Idempotency-Key` that
stays the same across retries, so a retried write is applied once. Pass
`retry=grepvine.RetryPolicy(...)` to change these bounds.

## Asynchronous use

`AsyncClient` takes the same arguments and has the same methods, awaited;
`client.index(...)` is an `AsyncIndexClient`, and the iterators are iterated
with `async for`. Create the client inside the event loop that will use it:

```python
import asyncio

import grepvine


async def main() -> None:
    async with grepvine.AsyncClient() as client:
        index = client.index("acme/support")
        await index.put_many([{"key": "a.txt", "content": "alpha"}])
        async for hit in index.search(pattern="alpha"):
            print(hit.key, hit.line_number)


asyncio.run(main())
```

## Organizations

Every operation is also a method of the client's resources:
`client.organizations` (with `members`), `client.indexes`,
`client.documents`, `client.search`, `client.api_keys`, `client.account` and
`client.device_login`. A method takes the path parameters (`organization`,
`index`, `key`, `user`) by position, and everything else by name, the same way
`IndexClient` does.

```python
client.organizations.create(name="my-org")  # you become its owner
print(client.organizations.get("my-org").role)  # owner

for org in client.organizations.list():
    print(org.name, org.role, org.suspended)

members = client.organizations.members
members.add("my-org", user="bob", role="developer")
members.add("my-org", user="carol", role="reader")
members.update("my-org", "bob", role="admin")
for member in members.list("my-org"):
    print(member.user.name, member.role)
members.remove("my-org", "carol")

client.organizations.transfer_ownership("my-org", user="bob")  # to a member; you become an admin
```

Only the owner deletes an organization, with
`client.organizations.delete("my-org")`. It reads as not found as soon as the
call returns; its data is removed in the background.

Organizations and user accounts share one namespace, so an organization name
must not be taken by a user either. Adding, changing and removing members
needs the admin or owner role; transferring ownership and deleting the
organization need the owner role.

A suspended organization keeps its data, but refuses every operation on its
members, indexes, documents and searches with `PermissionDeniedError` and code
`"organization_suspended"` until it is resumed. `organizations.get` and
`organizations.list` still answer, with `suspended` set. Contact support.

## API keys

A signed-in user manages their API keys through `client.api_keys`:

```python
key = client.api_keys.create(name="ci")  # 1 to 128 characters
print(key.key)  # the secret, shown only now

for listed in client.api_keys.list():
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
client = grepvine.Client(endpoint="https://grepvine.example.com", trust_env=False)

if client.account.username_availability("alice").available:
    client.account.register(name="alice", email="alice@example.com", password="a long passphrase")
client.account.login(identifier="alice", password="a long passphrase")

print(client.account.me().email)
client.account.change_password(current_password="a long passphrase", new_password="a longer one!")
client.account.logout()
```

`login` starts a session on the client: later requests carry its cookie and
CSRF token. A taken username or email address raises `ConflictError` with
code `"username_taken"` or `"email_taken"`, and wrong credentials raise
`AuthenticationError`. Passwords are at least 12 characters.

`account.auth_options()` reports whether anyone may register (`signup` is
`"open"`) or only with an invitation (`"invite"`). Then pass the invitation
link's token as `register(..., invitation=token)`; without one, `register`
raises `PermissionDeniedError` with code `"invitation_required"`, and with one
that was used, withdrawn or has expired, code `"invitation_invalid"`.
`account.check_invitation(token=token)` shows what a pending invitation offers
before registering.

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


endpoint = "https://api.grepvine.ai"  # or your Grepvine service
# trust_env=False: no API key from the environment or gv's file; starting needs none.
with grepvine.Client(endpoint=endpoint, trust_env=False) as anonymous:
    key = anonymous.device_login.authorize("my laptop", on_code=show, timeout=600)
client = grepvine.Client(api_key=key.key, endpoint=endpoint)
```

A denied login raises `InvalidRequestError` with code `"access_denied"`, and
an expired one with `"expired_token"`. A login that is not approved within
`timeout` seconds, or before it expires, raises `WaitTimeoutError`.

The steps are also available one at a time: the program calls
`device_login.start(api_key_name=...)` and `device_login.poll(device_code=...)`,
and the person, or a tool acting for them, calls `device_login.approve` or
`device_login.deny` with the `user_code`. `poll` raises `InvalidRequestError`
with code `"authorization_pending"` while the person has not decided, and
`"slow_down"` when polled more often than the authorization's `interval`.

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

A `Client` may be shared between threads. An iterator from a listing or a
search is not thread-safe.

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

The `examples` directory holds complete programs. They are configured like
`gv`, from `GREPVINE_API_KEY`, `GREPVINE_API_ENDPOINT` and
`GREPVINE_ORGANIZATION`, or from `~/.grepvine/config.yaml`:

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
