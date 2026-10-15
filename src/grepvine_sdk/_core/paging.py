"""Token-based pagination shared by every listing and by search."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field, replace
from types import ModuleType
from typing import Any, Final, Generic, TypeVar

from grepvine_sdk._core.effects import Call, Op
from grepvine_sdk._core.responses import parsed
from grepvine_sdk.errors import GrepvineError
from grepvine_sdk.models import Page

T = TypeVar("T")
U = TypeVar("U")

MAX_PAGE_SIZE: Final = 200
MAX_PAGE_TOKEN_LENGTH: Final = 4096


def resolve_page_size(page_size: int | None, limit: int | None) -> int:
    """Validate pagination arguments and choose the page size.

    Without an explicit ``page_size``, a ``limit`` below the maximum page size
    becomes the page size so the service stops as soon as enough results exist.
    """
    if limit is not None and limit < 0:
        raise ValueError("limit must not be negative")
    if page_size is None:
        page_size = MAX_PAGE_SIZE if not limit else min(MAX_PAGE_SIZE, limit)
    if not 1 <= page_size <= MAX_PAGE_SIZE:
        raise ValueError(f"page_size must be between 1 and {MAX_PAGE_SIZE}")
    return page_size


def validate_page_token(page: str | None) -> str | None:
    if not page:
        return None
    if len(page) > MAX_PAGE_TOKEN_LENGTH:
        raise ValueError("page token is too long")
    return page


@dataclass(frozen=True, slots=True, kw_only=True)
class PageSource(Generic[T]):
    """Everything needed to fetch any page of one listing or search.

    The page token the service issues is bound to the request's other
    arguments, so they are fixed here and repeated identically on every page.
    ``parse_item`` turns one decoded result into the item a paginator yields.
    """

    operation: ModuleType
    page_model: type[Any]
    args: tuple[Any, ...] = ()
    kwargs: Mapping[str, Any] = field(default_factory=dict)
    page_size: int
    limit: int | None
    start_page: str | None
    parse_item: Callable[[Any], T]

    @property
    def name(self) -> str:
        return self.operation.__name__.rsplit(".", 1)[-1]

    def request(self, token: str | None) -> Call:
        kwargs = {**self.kwargs, "amount": self.page_size}
        if token is not None:
            kwargs["page"] = token
        return Call(self.operation, self.args, kwargs)

    def map(self, convert: Callable[[T], U]) -> PageSource[U]:
        """The same listing, yielding each item passed through ``convert``."""
        parse = self.parse_item
        return PageSource(
            operation=self.operation,
            page_model=self.page_model,
            args=self.args,
            kwargs=self.kwargs,
            page_size=self.page_size,
            limit=self.limit,
            start_page=self.start_page,
            parse_item=lambda item: convert(parse(item)),
        )

    def cursor(self) -> PageCursor[T]:
        return PageCursor(self)


class PageCursor(Generic[T]):
    """The position of one iteration over a :class:`PageSource`."""

    def __init__(self, source: PageSource[T]) -> None:
        self._source = source
        self._remaining = source.limit
        self._token = source.start_page
        self._started = False

    def next_request(self) -> Call | None:
        """The request for the next page, or None when the iteration is complete."""
        if self._remaining == 0:
            return None
        if self._started and self._token is None:
            return None
        return self._source.request(self._token)

    def feed(self, page: Page[T]) -> Page[T]:
        """Record a fetched page and return it clipped to the remaining limit."""
        previous = self._token
        self._started = True
        if page.has_next:
            if page.next_page_id is None or page.next_page_id == previous:
                raise GrepvineError("the service did not advance to a new page of results")
            self._token = page.next_page_id
        else:
            self._token = None
        if self._remaining is None:
            return page
        results = page.results[: self._remaining]
        self._remaining -= len(results)
        if len(results) < len(page.results):
            self._token = None
        return replace(page, results=results)


def fetch_page(source: PageSource[T], request: Call) -> Op[Page[T]]:
    """Fetch one page. Every page model of the API has ``results`` and ``pagination``."""
    response = yield request
    body = parsed(response, source.page_model)
    pagination = body.pagination
    has_next = bool(pagination.has_next)
    token = pagination.next_page_id or None
    prefixes = getattr(body, "common_prefixes", None) or ()
    return Page(
        results=tuple(source.parse_item(item) for item in body.results),
        next_page_id=str(token) if has_next and token else None,
        has_next=has_next,
        page_size=source.page_size,
        common_prefixes=tuple(str(prefix) for prefix in prefixes),
    )
