from __future__ import annotations

from http import HTTPStatus

import pytest

from grepvine import GrepvineError
from grepvine._core import ops
from grepvine._core.responses import parsed
from grepvine._generated.models import MutationBatchResult, MutationResult
from grepvine._generated.types import Response


def _response(body: object, status: int = 200) -> Response[object]:
    return Response(status_code=HTTPStatus(status), content=b"", headers={}, parsed=body)


def test_parsed_checks_the_decoded_type() -> None:
    batch = MutationBatchResult(results=[MutationResult(key="a", revision="r")])
    assert parsed(_response(batch), MutationBatchResult) is batch
    with pytest.raises(GrepvineError, match="unexpected response"):
        parsed(_response(None, 204), MutationBatchResult)


def test_batch_results_must_match_the_request() -> None:
    batch = _response(MutationBatchResult(results=[MutationResult(key="a", revision="r")]))
    assert [result.key for result in ops._mutation_results(batch, 1)] == ["a"]
    with pytest.raises(GrepvineError, match="1 results for a batch of 2 documents"):
        ops._mutation_results(batch, 2)
