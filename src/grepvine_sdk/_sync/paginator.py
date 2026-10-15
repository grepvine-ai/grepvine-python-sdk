"""Synchronous iteration over pages of results."""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, Generic, NoReturn, TypeVar

from grepvine_sdk._core.paging import PageSource, fetch_page
from grepvine_sdk.models import Page

if TYPE_CHECKING:
    from grepvine_sdk._sync.client import Client

T = TypeVar("T")


class Paginator(Generic[T]):
    """Every result of a listing or search, fetched page by page as it is iterated.

    Iterating yields items; :meth:`pages` yields :class:`~grepvine_sdk.models.Page`
    objects whose ``next_page_id`` lets a later call continue where this one
    stopped. Nothing is requested until iteration starts, and each iteration
    starts over from the beginning.
    """

    def __init__(self, client: Client, source: PageSource[T]) -> None:
        self._client = client
        self._source = source

    @property
    def page_size(self) -> int:
        return self._source.page_size

    @property
    def limit(self) -> int | None:
        return self._source.limit

    def pages(self) -> Iterator[Page[T]]:
        """Yield each page, including an empty page that the service says has more after it."""
        cursor = self._source.cursor()
        while (spec := cursor.next_request()) is not None:
            yield cursor.feed(self._client._run(fetch_page(self._source, spec)))

    def __iter__(self) -> Iterator[T]:
        for page in self.pages():
            yield from page.results

    def first(self) -> T | None:
        """The first result, or None when there is none."""
        return next(iter(self), None)

    def __aiter__(self) -> NoReturn:
        raise TypeError("this Paginator is synchronous; use 'for', or AsyncClient for 'async for'")

    def __repr__(self) -> str:
        return f"<Paginator {self._source.name} page_size={self.page_size}>"
