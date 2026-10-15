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
from wherever your application keeps them. The module-level functions such as
`grepvine.indexes` use a default client that you set up with `configure`:

```python
grepvine.configure(api_key="gvk_...")
```

A `Client` also takes `timeout` (seconds, or an `httpx.Timeout`) and `retry` (a
`RetryPolicy`). An endpoint may be given with or without `/v1`. A missing API
key raises `ConfigurationError` on the first request that needs one. To obtain
a key without a browser session, see [Device login](#device-login).

## Organizations

```python
import grepvine

for org in grepvine.organizations.list():
    print(org.name, org.role)

org = grepvine.organizations.get("my-org")
```

A client can also create and delete organizations, transfer their ownership,
and manage their members:

```python
client = grepvine.Client()

client.organizations.create("my-org")  # the caller becomes its owner

members = client.organizations.members("my-org")
members.add("bob", "developer")  # "admin", "developer" or "reader"
members.update("bob", "admin")
for member in members.list():
    print(member.user.name, member.role)
members.remove("bob")

client.organizations.transfer_ownership("my-org", "carol")  # the old owner becomes an admin
client.organizations.delete("my-org")  # deletion completes in the background
```

Organizations and user accounts share one namespace, so an organization name
must not be taken by a user either. Adding, changing and removing members
needs the admin or owner role; transferring ownership and deleting the
organization need the owner role.

## Indexes

Indexes are referenced as `"organization/index"`.

```python
index = client.indexes.create(
    "my-org/my-index",
    description="# Product docs\n\nEvery guide we publish.",  # Markdown, optional
    tags={"team": "search", "commit": "3f9c2a1"},  # key/value labels, optional
    exist_ok=True,
    wait=True,  # return once the index is ready
)
index = client.indexes.get("my-org/my-index")
print(index.state, index.document_count)
print(index.description)
print(index.tags["commit"])

for index in client.indexes.list("my-org"):
    print(f"{index.name}: {index.document_count} documents")
docs_indexes = list(client.indexes.list("my-org", prefix="docs-"))  # names starting with docs-

index = index.update(description="Guides, runbooks and the API reference.")
index = index.update(tags={"team": "platform", "commit": None})  # set one, remove one
index = index.set_tags({"commit": "8b1d0e4"})
index = index.remove_tags("team")
index = index.wait_until_ready(timeout=60)
index.exists()
index.delete()  # deletion completes in the background
```

A new index is `creating` for a moment before it is `ready`.
`indexes.create(..., wait=True)` and `index.wait_until_ready()` read the
index until it is ready and return a handle with its current state; they raise
`TimeoutError` after `timeout` seconds (300 by default, `None` for no limit)
and `GrepvineError` for an index that is being deleted.

`document_count` and the other counters are a snapshot from when the handle
was fetched; `index.refresh()` returns a new handle. An index's `description`
is Markdown, at most 16,384 characters, and empty when none was set;
`index.update(description=...)` replaces it (an empty string clears it) and
returns a new handle. An index's `tags` are a read-only mapping of key/value
labels, empty when none was set. `index.update(tags=...)` merges into them:
every key given is set, a key given as `None` is removed, and keys left out
stay as they are; `set_tags(...)` and `remove_tags(...)` are shorthands for
those two cases. `update` sends only the fields you pass, so changing the
description leaves the tags alone and the other way round. Changing a
description or tags needs the admin or owner role.

## Search

```python
index = client.indexes.get("my-org/my-index")

for result in index.search("TODO|FIXME"):
    print(f"{result.key}:{result.line_number}: {result.text}")

for result in index.search(
    "hello world",
    regex=False,  # literal text instead of a regular expression
    case_sensitive=False,
    whole_word=True,  # literal mode only
    multiline=False,  # True lets a match span lines
    filters=["path STARTSWITH 'src/'", "size < 100000"],
    lines_before=2,
    lines_after=2,
):
    for line in result.lines_before:
        print(f"{result.key}-{line.line_number}-{line.text}")
    print(f"{result.key}:{result.line_number}:{result.text}")
    print(result.match_texts())
```

A `SearchResult` carries the covered `text`, its `line_number`, and the
`matches` as byte offsets within the document, which is what the API reports.
`result.match_spans()` converts them to character positions within `text`,
and `result.match_texts()` returns the matched strings.

Filters are expressions over document metadata, such as
`path STARTSWITH 'docs/' AND mtime >= (CURRENT_DATE - INTERVAL '3 days')`. Several
`filters` are joined with `AND`; a single expression can be passed as `filter`.
The SDK records `path` and `size` metadata on every document it stores, so
filters on those fields work without extra effort.

## Documents

```python
from pathlib import Path

documents = index.documents

# Store one document: bytes, text, a path, or a binary file object.
documents.put("notes/today.md", content=b"# Today\n")
documents.put("report.pdf", content=Path("report.pdf"), metadata={"team": "sales"})

# Store several at once.
documents.put(
    [
        {"key": "a.txt", "content": "alpha"},
        {"key": "b.txt", "content": b"beta", "metadata": {"lang": "el"}},
    ]
)

# Read.
data = documents.get("notes/today.md")  # bytes
text = documents.get("notes/today.md", mode="r")  # str
head = documents.get("report.pdf", range=(0, 1023))
document = documents.fetch("notes/today.md")  # content, revision, metadata

# List.
for doc in documents.list(prefix="notes/"):
    print(doc.key, doc.size, doc.searchable)
for page in documents.list(delimiter="/").pages():
    print(page.common_prefixes)

# Delete.
documents.delete("notes/today.md")
documents.delete(["a.txt", "b.txt"])
```

Metadata values may be `str`, `int`, `float`, `bool`, or `datetime`; the SDK
tags them for the API and untags them on the way back. Documents may carry up
to 64 metadata fields, two of which the SDK uses for `path` and `size` (and a
third, `mtime`, when the content is a path). Your fields override those.

Documents can be up to 1 GiB. Content that is valid UTF-8 and at most 100 MiB
is searchable; anything else is stored and served but never matched by a
search. `DocumentSummary.searchable` reports which applies.

Preconditions are available on every write: `if_match=revision` applies the
change only if the document still has that revision, and `if_none_match=True`
only if the document does not exist. A single-document write whose
precondition fails raises `PreconditionFailedError`. In the list forms, put
these inside each mapping; a document whose precondition fails is reported in
its result instead, as described under "Results of list writes" below.

### Results of list writes

The list form of `put`, and the list form of `delete`, return one
`MutationResult` per document, in input order. Each document is written on
its own. A document whose `if_match` or `if_none_match` condition fails is
left unchanged and the others are written; a list `delete` does the same with
a key that does not exist. The result of a written document has its new
`revision`. The result of an unchanged document has no revision, `ok` is
`False`, and `error` says why: its `code` is `"precondition_failed"` or
`"not_found"`, and its `message` is the service's explanation.

```python
results = documents.put(
    [
        {"key": "a.txt", "content": "alpha", "if_none_match": True},
        {"key": "b.txt", "content": "beta", "if_match": revision},
    ]
)
for result in results:
    if result.error:
        print(f"{result.key} was not stored: {result.error.message}")

missing = [result.key for result in documents.delete(["a.txt", "gone.txt"]) if not result.ok]
```

Text documents travel in batches of up to 2,048 documents and 16 MiB, and
binary or larger documents travel one at a time. If a request fails after
earlier requests got an answer, for example because the service failed on
every attempt, the SDK raises `PartialBatchError`. It has `committed` (the
results so far, unchanged documents included), `failed_keys` (the documents of
the failed request; the service may have written some of them), and
`pending_keys` (the documents that were never sent). If the first request
fails, the SDK raises the underlying error unchanged. To finish an interrupted
write safely, give it an `idempotency_key` and repeat it with the same key and
the same documents: the service does not write a document twice.

## Pagination

Every `list` and `search` returns a paginator. Iterating it yields every
result, fetching pages as needed:

```python
for doc in documents.list():
    ...
```

`limit` caps the number of results yielded. `page_size` (1 to 200) sets how
many results each request asks for. `pages()` yields `Page` objects, and a
page's `next_page_id` lets a later call continue from it:

```python
page = next(iter(documents.list(page_size=100).pages()))
later = documents.list(page=page.next_page_id, page_size=page.page_size)
```

A continuation is valid for 15 minutes and only with the same arguments,
including `page_size`; otherwise the service answers with `InvalidPageError`.
A search page may be empty while more results follow; the paginator keeps
going until the service reports the end.

## Errors

Every error is a `GrepvineError`. Errors from the service are `APIError`
subclasses with `status_code`, `code`, `message`, and `request_id`:

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

`ConfigurationError` means the client has no API key or an unusable endpoint
or configuration file. `TransportError` means the request could not be
delivered. `PartialBatchError` is described above.

The SDK retries on its own: a `429` pauses every request of the client for the
interval the service asks for (with jitter, up to a minute at a time and ten
minutes in total per request), and a `5xx` answer or a connection failure is
retried twice more with a short backoff. Every write carries an idempotency
key that stays the same across retries, so a retried write is applied once.
Pass `retry=grepvine.RetryPolicy(...)` to change these bounds.

## Asynchronous use

`AsyncClient` has the same methods, awaited, and its paginators support
`async for`. Create it inside the event loop that will use it:

```python
import asyncio

import grepvine


async def main() -> None:
    async with grepvine.AsyncClient() as client:
        index = await client.indexes.get("my-org/my-index")
        async for result in index.search("hello"):
            print(result.key, result.line_number)
        await index.documents.put("a.txt", content=b"alpha")


asyncio.run(main())
```

## API keys

A signed-in user manages their API keys through `client.api_keys`:

```python
key = client.api_keys.create("ci")  # 1 to 128 characters
print(key.key)  # the secret, shown only now

for listed in client.api_keys.list():
    print(listed.id, listed.name, listed.prefix, listed.last_used_at, listed.revoked)

client.api_keys.revoke(key.id)
```

A listing shows each key's `prefix`, never its secret. A revoked key stays in
the listing with its `revoked_at` time, and requests that use it fail with
`AuthenticationError`.

## Account

`client.account` registers users, signs them in and out, and changes their
password. The API key is the way to authenticate everything else; a session is
for scripts that start from a username and password, such as end-to-end tests
that create an account and its first API key.

```python
client = grepvine.Client(endpoint="https://grepvine.example.com")

if client.account.username_available("alice"):
    client.account.register("alice", "alice@example.com", "a long passphrase")
else:
    client.account.login("alice", "a long passphrase")  # username or email address

print(client.account.me().email)
key = client.api_keys.create("tests")
client.account.change_password("a long passphrase", "a longer passphrase")
client.account.logout()
```

`register` and `login` start a session and keep it on the client: later
requests carry the session and its CSRF token instead of the API key, until
`logout` ends it. A taken username or email address raises `ConflictError`
with code `"username_taken"` or `"email_taken"`, and wrong credentials raise
`AuthenticationError`. Passwords are at least 12 characters.

## Device login

Device login gives an API key to a program, such as a command-line tool or an
agent, once a person approves it in a signed-in browser. `authorize` does the
program's part in one call: it starts the login, hands the code to `on_code`
to show, and waits for the person's decision, polling at the interval the
service asks for.

```python
def show(authorization: grepvine.DeviceAuthorization) -> None:
    print(f"Open {authorization.verification_uri_complete}")
    print(f"and check that it shows {authorization.user_code}")


key = client.device_login.authorize("my laptop", on_code=show, timeout=600)
client.configure(api_key=key.key)
```

A denied login raises `InvalidRequestError` with code `"access_denied"`, and
an expired one with `"expired_token"`. A login that is not approved within
`timeout` seconds, or before it expires, raises `TimeoutError`. Starting a
device login needs no API key; with `AsyncClient`, `on_code` may also be a
coroutine function.

The steps are also available one at a time. The program calls `start` and
`poll`; the person, or a tool acting for them with an API key or a session,
calls `approve` or `deny` with the code:

```python
authorization = client.device_login.start("my laptop")
key = client.device_login.poll(authorization.device_code)  # None until approved

admin.device_login.approve(authorization.user_code)  # or deny(...)
```

`poll` returns `None` while the person has not decided. Polling more often
than the authorization's `interval` raises `InvalidRequestError` with code
`"slow_down"`.

## Other requests

`client.http` is an `httpx.Client` (an `httpx.AsyncClient` for `AsyncClient`)
set up with the client's endpoint, credentials, timeout and retries. Use it
for anything the resources above do not cover, such as streaming a large
document to a file:

```python
from urllib.parse import quote

path = f"/organizations/my-org/indexes/my-index/objects/{quote('videos/demo.mp4', safe='')}"
with client.http.stream("GET", path) as response:
    response.raise_for_status()
    with open("demo.mp4", "wb") as file:
        for chunk in response.iter_bytes():
            file.write(chunk)
```

Paths are relative to the endpoint's `/v1`. Responses come back as they are,
errors included.

## Thread safety

A `Client` may be shared between threads. Paginators are not thread-safe;
each iteration of a paginator starts over from the beginning.

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
searches them one result per page and with a metadata filter, and deletes the
index at the end. The organization must exist, and the key needs permission
to create and delete indexes.

## License

Proprietary. See `LICENSE`.
