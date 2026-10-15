from __future__ import annotations

import io
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

import grepvine_sdk._core.batching as batching
import grepvine_sdk._core.ops as ops_module
from grepvine_sdk import (
    Document,
    DocumentSummary,
    MutationResult,
    NotFoundError,
    PartialBatchError,
    PreconditionFailedError,
    RangeNotSatisfiableError,
    ServerError,
)
from tests.conftest import Flavor
from tests.fake_server import FakeGrepvine

pytestmark = pytest.mark.anyio


@pytest.fixture
def index(fake: FakeGrepvine) -> str:
    fake.add_index("acme/docs")
    return "acme/docs"


async def _documents(fx: Flavor, ref: str):
    return (await fx.run(fx.client.indexes.get(ref))).documents


def _stored(fake: FakeGrepvine, key: str) -> Any:
    return fake.indexes[("acme", "docs")].documents[key]


async def test_put_bytes_uses_multipart_and_default_metadata(
    fx: Flavor, fake: FakeGrepvine, index: str
) -> None:
    documents = await _documents(fx, index)

    result = await fx.run(documents.put("notes/a.txt", content=b"hello world"))

    assert isinstance(result, MutationResult)
    assert result.key == "notes/a.txt"
    stored = _stored(fake, "notes/a.txt")
    assert stored.content == b"hello world"
    assert stored.metadata == {
        "path": {"type": "string", "value": "notes/a.txt"},
        "size": {"type": "integer", "value": 11},
    }
    request = fake.requests[-1]
    assert request.method == "PUT"
    assert request.url.path == "/v1/organizations/acme/indexes/docs/objects"
    assert request.headers["content-type"].startswith("multipart/form-data")
    assert len(request.headers["idempotency-key"]) == 32


async def test_put_text_and_user_metadata(fx: Flavor, fake: FakeGrepvine, index: str) -> None:
    documents = await _documents(fx, index)
    when = datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC)

    await fx.run(
        documents.put(
            "a.txt",
            content="héllo",
            metadata={"path": "custom", "n": 3, "ratio": 0.5, "ok": True, "when": when},
        )
    )

    stored = _stored(fake, "a.txt")
    assert stored.content == "héllo".encode()
    assert stored.metadata == {
        "path": {"type": "string", "value": "custom"},
        "size": {"type": "integer", "value": 6},
        "n": {"type": "integer", "value": 3},
        "ratio": {"type": "number", "value": 0.5},
        "ok": {"type": "boolean", "value": True},
        "when": {"type": "timestamp", "value": "2026-01-02T03:04:05Z"},
    }


async def test_put_from_path_records_mtime(
    fx: Flavor, fake: FakeGrepvine, index: str, tmp_path: Path
) -> None:
    file = tmp_path / "big.bin"
    file.write_bytes(b"\x00\x01\x02" * 10)
    documents = await _documents(fx, index)

    await fx.run(documents.put("big.bin", content=file))

    stored = _stored(fake, "big.bin")
    assert stored.content == b"\x00\x01\x02" * 10
    assert stored.metadata["size"] == {"type": "integer", "value": 30}
    assert stored.metadata["mtime"]["type"] == "timestamp"
    assert stored.metadata["mtime"]["value"].endswith("Z")


async def test_put_from_file_objects(fx: Flavor, fake: FakeGrepvine, index: str) -> None:
    documents = await _documents(fx, index)
    seekable = io.BytesIO(b"skip-me;payload")
    seekable.seek(8)
    await fx.run(documents.put("seekable", content=seekable))
    assert _stored(fake, "seekable").content == b"payload"
    assert _stored(fake, "seekable").metadata["size"]["value"] == 7

    class Stream:
        def read(self) -> bytes:
            return b"streamed"

    await fx.run(documents.put("stream", content=Stream()))
    assert _stored(fake, "stream").content == b"streamed"

    await fx.run(documents.put("view", content=memoryview(b"viewed")))
    assert _stored(fake, "view").content == b"viewed"


async def test_put_rejects_unusable_content(fx: Flavor, index: str) -> None:
    documents = await _documents(fx, index)
    with pytest.raises(TypeError, match="content must be"):
        await fx.run(documents.put("k", content=123))

    class TextStream:
        def read(self) -> str:
            return "text"

    with pytest.raises(TypeError, match="binary mode"):
        await fx.run(documents.put("k", content=TextStream()))
    with pytest.raises(TypeError, match="needs content"):
        await fx.run(documents.put("k"))


async def test_put_preconditions(fx: Flavor, fake: FakeGrepvine, index: str) -> None:
    documents = await _documents(fx, index)
    first = await fx.run(documents.put("a.txt", content=b"1", if_none_match=True))

    assert first.ok
    assert first.error is None

    with pytest.raises(PreconditionFailedError) as excinfo:
        await fx.run(documents.put("a.txt", content=b"2", if_none_match=True))
    assert (excinfo.value.status_code, excinfo.value.code) == (412, "precondition_failed")
    assert fake.requests[-1].headers["if-none-match"] == "*"

    with pytest.raises(PreconditionFailedError):
        await fx.run(documents.put("a.txt", content=b"2", if_match="stale"))
    second = await fx.run(documents.put("a.txt", content=b"2", if_match=first.revision))
    assert second.revision != first.revision
    assert fake.requests[-1].headers["if-match"] == first.revision

    with pytest.raises(ValueError, match="cannot be combined"):
        await fx.run(documents.put("a.txt", content=b"3", if_match="r", if_none_match=True))


async def test_put_custom_idempotency_key(fx: Flavor, fake: FakeGrepvine, index: str) -> None:
    documents = await _documents(fx, index)
    key = "my-operation-0001"
    await fx.run(documents.put("a.txt", content=b"1", idempotency_key=key))
    assert fake.requests[-1].headers["idempotency-key"] == key
    with pytest.raises(ValueError, match="16 to 128"):
        await fx.run(documents.put("a.txt", content=b"1", idempotency_key="short"))


async def test_put_list_batches_text_and_uploads_binary_in_order(
    fx: Flavor, fake: FakeGrepvine, index: str
) -> None:
    documents = await _documents(fx, index)

    results = await fx.run(
        documents.put(
            [
                {"key": "a.txt", "content": b"alpha"},
                {"key": "b.txt", "content": "beta", "metadata": {"lang": "el"}},
                {"key": "c.bin", "content": b"\xff\xfe"},
                {"key": "d.txt", "content": "delta"},
            ]
        )
    )

    assert [result.key for result in results] == ["a.txt", "b.txt", "c.bin", "d.txt"]
    assert [request.method for request in fake.requests[1:]] == ["POST", "PUT", "POST"]
    batch = fake.requests[1]
    assert batch.url.path.endswith("/objects:batch")
    assert batch.headers["content-type"] == "application/x-ndjson"
    records = [json.loads(line) for line in batch.content.splitlines()]
    assert [record["key"] for record in records] == ["a.txt", "b.txt"]
    assert records[1]["metadata"]["lang"] == {"type": "string", "value": "el"}
    assert records[1]["metadata"]["path"] == {"type": "string", "value": "b.txt"}
    assert _stored(fake, "c.bin").content == b"\xff\xfe"
    assert _stored(fake, "d.txt").content == b"delta"
    keys = {request.headers["idempotency-key"] for request in fake.requests[1:]}
    assert len(keys) == 3


async def test_put_list_with_preconditions_in_records(
    fx: Flavor, fake: FakeGrepvine, index: str
) -> None:
    documents = await _documents(fx, index)
    [first] = await fx.run(documents.put([{"key": "a.txt", "content": "1", "if_none_match": True}]))
    record = json.loads(fake.requests[-1].content)
    assert record["if_none_match"] == "*"

    [stale] = await fx.run(documents.put([{"key": "a.txt", "content": "2", "if_match": "stale"}]))
    assert (stale.key, stale.ok, stale.revision) == ("a.txt", False, None)
    assert stale.error is not None
    assert stale.error.code == "precondition_failed"
    assert _stored(fake, "a.txt").content == b"1"

    [fresh] = await fx.run(
        documents.put([{"key": "a.txt", "content": "2", "if_match": first.revision}])
    )
    assert fresh.ok
    assert _stored(fake, "a.txt").content == b"2"


async def test_put_list_reports_each_document(fx: Flavor, fake: FakeGrepvine, index: str) -> None:
    existing = fake.add_document(index, "a.txt", "old")
    fake.add_document(index, "c.bin", b"\xff")
    documents = await _documents(fx, index)

    results = await fx.run(
        documents.put(
            [
                {"key": "a.txt", "content": "new", "if_match": "stale"},
                {"key": "b.txt", "content": "beta"},
                {"key": "c.bin", "content": b"\xfe", "if_none_match": True},
                {"key": "d.txt", "content": "delta", "if_none_match": True},
            ]
        )
    )

    # Two batches and one upload between them; a failed condition stops neither.
    assert [request.method for request in fake.requests[1:]] == ["POST", "PUT", "POST"]
    assert [result.key for result in results] == ["a.txt", "b.txt", "c.bin", "d.txt"]
    assert [result.ok for result in results] == [False, True, False, True]
    failed = [result for result in results if result.error is not None]
    assert [(r.key, r.error.code, r.revision) for r in failed if r.error] == [
        ("a.txt", "precondition_failed", None),
        ("c.bin", "precondition_failed", None),
    ]
    assert str(failed[0].error).endswith("(precondition_failed)")
    assert all(result.revision for result in results if result.ok)
    assert _stored(fake, "a.txt").revision == existing.revision
    assert _stored(fake, "c.bin").content == b"\xff"
    assert _stored(fake, "b.txt").content == b"beta"
    assert _stored(fake, "d.txt").content == b"delta"


async def test_put_list_empty_sends_nothing(fx: Flavor, fake: FakeGrepvine, index: str) -> None:
    documents = await _documents(fx, index)
    before = len(fake.requests)
    assert await fx.run(documents.put([])) == []
    assert len(fake.requests) == before


async def test_put_list_splits_by_record_count(
    fx: Flavor, fake: FakeGrepvine, index: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(batching, "MAX_BATCH_RECORDS", 2)
    documents = await _documents(fx, index)

    results = await fx.run(
        documents.put([{"key": f"{n}.txt", "content": f"doc {n}"} for n in range(5)])
    )

    assert [result.key for result in results] == [f"{n}.txt" for n in range(5)]
    batches = [request for request in fake.requests if request.url.path.endswith(":batch")]
    assert [len(request.content.splitlines()) for request in batches] == [2, 2, 1]


async def test_put_list_splits_by_content_bytes(
    fx: Flavor, fake: FakeGrepvine, index: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(batching, "MAX_BATCH_CONTENT_BYTES", 10)
    documents = await _documents(fx, index)

    await fx.run(
        documents.put(
            [
                {"key": "a", "content": "123456"},
                {"key": "b", "content": "7890"},
                {"key": "c", "content": "x"},
                {"key": "big", "content": "y" * 11},
            ]
        )
    )

    methods = [request.method for request in fake.requests[1:]]
    assert methods == ["POST", "POST", "PUT"]
    assert [len(r.content.splitlines()) for r in fake.requests[1:3]] == [2, 1]
    assert _stored(fake, "big").content == b"y" * 11


async def test_put_list_partial_failure(
    fx: Flavor, fake: FakeGrepvine, index: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(batching, "MAX_BATCH_RECORDS", 2)
    documents = await _documents(fx, index)
    fake.fail_next(500, times=3, when=lambda request: b'"key": "c"' in request.content)

    with pytest.raises(PartialBatchError) as excinfo:
        await fx.run(
            documents.put([{"key": k, "content": f"doc {k}"} for k in ["a", "b", "c", "d", "e"]])
        )

    error = excinfo.value
    assert [result.key for result in error.committed] == ["a", "b"]
    assert error.failed_keys == ("c", "d")
    assert error.pending_keys == ("e",)
    assert isinstance(error.__cause__, ServerError)
    assert "2 document(s) failed after 2 were written and 1 were not attempted" in str(error)
    assert set(fake.indexes[("acme", "docs")].documents) == {"a", "b"}


async def test_put_list_partial_failure_counts_unchanged_documents(
    fx: Flavor, fake: FakeGrepvine, index: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(batching, "MAX_BATCH_RECORDS", 2)
    documents = await _documents(fx, index)
    fake.fail_next(500, times=3, when=lambda request: b'"key": "c"' in request.content)
    records: list[dict[str, Any]] = [{"key": k, "content": f"doc {k}"} for k in "abcde"]
    records[0]["if_match"] = "stale"

    with pytest.raises(PartialBatchError) as excinfo:
        await fx.run(documents.put(records))

    error = excinfo.value
    assert [(result.key, result.ok) for result in error.committed] == [("a", False), ("b", True)]
    assert "failed after 1 were written, 1 were left unchanged, and 1 were not" in str(error)


async def test_put_list_first_failure_propagates_unwrapped(
    fx: Flavor, fake: FakeGrepvine, index: str
) -> None:
    documents = await _documents(fx, index)
    fake.fail_next(500, times=3, path_suffix=":batch")
    with pytest.raises(ServerError):
        await fx.run(documents.put([{"key": "a", "content": "x"}]))


async def test_put_list_validates_records(fx: Flavor, index: str) -> None:
    documents = await _documents(fx, index)
    with pytest.raises(ValueError, match="non-empty string 'key'"):
        await fx.run(documents.put([{"content": "x"}]))
    with pytest.raises(ValueError, match="needs 'content'"):
        await fx.run(documents.put([{"key": "a"}]))
    with pytest.raises(ValueError, match="unknown field"):
        await fx.run(documents.put([{"key": "a", "content": "x", "bogus": 1}]))
    with pytest.raises(ValueError, match="cannot be combined"):
        await fx.run(
            documents.put([{"key": "a", "content": "x", "if_match": "r", "if_none_match": True}])
        )
    with pytest.raises(ValueError, match="if_match must be a string"):
        await fx.run(documents.put([{"key": "a", "content": "x", "if_match": 1}]))
    with pytest.raises(TypeError, match="must be a mapping"):
        await fx.run(documents.put(["a.txt"]))
    with pytest.raises(TypeError, match="inside each document"):
        await fx.run(documents.put([{"key": "a", "content": "x"}], metadata={"a": 1}))


async def test_get_returns_bytes_or_text(fx: Flavor, fake: FakeGrepvine, index: str) -> None:
    fake.add_document(
        index, "dir/a.txt", "héllo wörld", {"path": {"type": "string", "value": "dir/a.txt"}}
    )
    documents = await _documents(fx, index)

    assert await fx.run(documents.get("dir/a.txt")) == "héllo wörld".encode()
    assert await fx.run(documents.get("dir/a.txt", mode="r")) == "héllo wörld"
    assert fake.requests[-1].url.raw_path.endswith(b"/objects/dir%2Fa.txt")
    with pytest.raises(ValueError, match="mode"):
        await fx.run(documents.get("dir/a.txt", mode="w"))


async def test_fetch_returns_revision_metadata_and_range(
    fx: Flavor, fake: FakeGrepvine, index: str
) -> None:
    stored = fake.add_document(
        index,
        "a.txt",
        b"0123456789",
        {"path": {"type": "string", "value": "a.txt"}, "size": {"type": "integer", "value": 10}},
    )
    documents = await _documents(fx, index)

    document = await fx.run(documents.fetch("a.txt"))
    assert isinstance(document, Document)
    assert document.revision == stored.revision
    assert document.metadata == {"path": "a.txt", "size": 10}
    assert document.size == 10
    assert document.content_range is None
    assert bytes(document) == b"0123456789"
    assert document.text() == "0123456789"

    fake.quote_etag = True
    partial = await fx.run(documents.fetch("a.txt", range=(2, 4)))
    assert partial.content == b"234"
    assert partial.revision == stored.revision
    assert partial.content_range == (2, 4, 10)
    assert partial.size == 10
    assert fake.requests[-1].headers["range"] == "bytes=2-4"

    assert await fx.run(documents.get("a.txt", range=(None, 3))) == b"789"
    assert fake.requests[-1].headers["range"] == "bytes=-3"
    assert await fx.run(documents.get("a.txt", range=(7, None))) == b"789"
    assert fake.requests[-1].headers["range"] == "bytes=7-"

    with pytest.raises(RangeNotSatisfiableError):
        await fx.run(documents.get("a.txt", range=(50, 60)))
    with pytest.raises(ValueError, match="start, an end, or both"):
        await fx.run(documents.get("a.txt", range=(None, None)))
    with pytest.raises(ValueError, match="must not precede"):
        await fx.run(documents.get("a.txt", range=(5, 2)))
    with pytest.raises(NotFoundError):
        await fx.run(documents.get("missing"))


async def test_list_folds_prefixes(fx: Flavor, fake: FakeGrepvine, index: str) -> None:
    for key in ["src/a.py", "src/lib/b.py", "src/lib/c.py", "README.md"]:
        fake.add_document(index, key, "x")
    fake.add_document(index, "img.bin", b"\xff\xfe")
    documents = await _documents(fx, index)

    everything = await fx.collect(documents.list())
    assert [doc.key for doc in everything] == [
        "README.md",
        "img.bin",
        "src/a.py",
        "src/lib/b.py",
        "src/lib/c.py",
    ]
    assert all(isinstance(doc, DocumentSummary) for doc in everything)
    assert everything[0].size == 1
    assert everything[0].searchable is True
    assert everything[1].searchable is False

    pages = await fx.collect(documents.list(prefix="src/", delimiter="/").pages())
    assert len(pages) == 1
    assert [doc.key for doc in pages[0].results] == ["src/a.py"]
    assert pages[0].common_prefixes == ("src/lib/",)
    params = fake.requests[-1].url.params
    assert (params["prefix"], params["delimiter"]) == ("src/", "/")

    with pytest.raises(ValueError, match="delimiter"):
        documents.list(delimiter="")


async def test_delete_single(fx: Flavor, fake: FakeGrepvine, index: str) -> None:
    stored = fake.add_document(index, "a/b.txt", "x")
    documents = await _documents(fx, index)

    with pytest.raises(PreconditionFailedError):
        await fx.run(documents.delete("a/b.txt", if_match="stale"))
    result = await fx.run(documents.delete("a/b.txt", if_match=stored.revision))

    assert result.key == "a/b.txt"
    request = fake.requests[-1]
    assert request.method == "DELETE"
    assert request.url.raw_path.endswith(b"/objects/a%2Fb.txt")
    assert len(request.headers["idempotency-key"]) == 32
    with pytest.raises(NotFoundError):
        await fx.run(documents.delete("a/b.txt"))


async def test_delete_many(
    fx: Flavor, fake: FakeGrepvine, index: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(ops_module, "MAX_BATCH_RECORDS", 2)
    stored = fake.add_document(index, "a", "x")
    for key in ["b", "c", "d"]:
        fake.add_document(index, key, "x")
    documents = await _documents(fx, index)

    results = await fx.run(documents.delete(["a", {"key": "b", "if_match": None}, "c", "missing"]))

    assert [result.key for result in results] == ["a", "b", "c", "missing"]
    assert [result.ok for result in results] == [True, True, True, False]
    assert results[3].error is not None
    assert results[3].error.code == "not_found"
    assert results[3].revision is None
    posts = [r for r in fake.requests if r.url.path.endswith(":delete")]
    assert len(posts) == 2
    assert json.loads(posts[0].content) == {"objects": [{"key": "a"}, {"key": "b"}]}
    assert set(fake.indexes[("acme", "docs")].documents) == {"d"}

    assert await fx.run(documents.delete([])) == []
    [stale] = await fx.run(documents.delete([{"key": "d", "if_match": stored.revision}]))
    assert stale.error is not None
    assert stale.error.code == "precondition_failed"
    assert "d" in fake.indexes[("acme", "docs")].documents


async def test_delete_many_partial_failure(
    fx: Flavor, fake: FakeGrepvine, index: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(ops_module, "MAX_BATCH_RECORDS", 1)
    documents = await _documents(fx, index)
    fake.fail_next(500, times=3, when=lambda request: b'"key":"b"' in request.content)

    with pytest.raises(PartialBatchError) as excinfo:
        await fx.run(documents.delete(["a", "b", "c"]))
    assert [r.key for r in excinfo.value.committed] == ["a"]
    assert excinfo.value.failed_keys == ("b",)
    assert excinfo.value.pending_keys == ("c",)

    fake.fail_next(500, times=3, path_suffix=":delete")
    with pytest.raises(ServerError):
        await fx.run(documents.delete(["a"]))


async def test_delete_validates_input(fx: Flavor, index: str) -> None:
    documents = await _documents(fx, index)
    with pytest.raises(ValueError, match="must not be empty"):
        await fx.run(documents.delete([""]))
    with pytest.raises(ValueError, match="unknown field"):
        await fx.run(documents.delete([{"key": "a", "bogus": 1}]))
    with pytest.raises(ValueError, match="non-empty string 'key'"):
        await fx.run(documents.delete([{"if_match": "r"}]))
    with pytest.raises(ValueError, match="if_match must be a string"):
        await fx.run(documents.delete([{"key": "a", "if_match": 3}]))
    with pytest.raises(TypeError, match="must be a key or a mapping"):
        await fx.run(documents.delete([3]))
    with pytest.raises(TypeError, match="inside each mapping"):
        await fx.run(documents.delete(["a"], if_match="r"))
    with pytest.raises(ValueError, match="must not be empty"):
        await fx.run(documents.delete(""))
    assert repr(documents).endswith("acme/docs>")
