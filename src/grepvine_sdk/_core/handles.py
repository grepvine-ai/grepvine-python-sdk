"""The read-only view of an index shared by the synchronous and asynchronous handles."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from types import MappingProxyType

from grepvine_sdk.models import IndexData


class IndexFields:
    """Exposes the fields of an :class:`~grepvine_sdk.models.IndexData` snapshot."""

    _data: IndexData

    @property
    def data(self) -> IndexData:
        """The index as the API reported it when this handle was created."""
        return self._data

    @property
    def id(self) -> str:
        return self._data.id

    @property
    def organization(self) -> str:
        return self._data.organization

    @property
    def name(self) -> str:
        return self._data.name

    @property
    def ref(self) -> str:
        """The ``organization/name`` reference of this index."""
        return self._data.ref

    @property
    def canonical_id(self) -> str:
        return self._data.canonical_id

    @property
    def description(self) -> str:
        """What the index holds, in Markdown; empty when no description was set.

        Change it with ``update(description=...)``, which returns a new handle.
        """
        return self._data.description

    @property
    def tags(self) -> Mapping[str, str]:
        """The index's key/value labels as of this handle; empty when none was set.

        The mapping is read-only. Change tags with ``update(tags=...)``,
        ``set_tags(...)`` or ``remove_tags(...)``, each of which returns a new
        handle.
        """
        return MappingProxyType(self._data.tags)

    @property
    def state(self) -> str:
        return self._data.state

    @property
    def document_count(self) -> int:
        """How many documents the index held when this handle was created."""
        return self._data.document_count

    @property
    def content_bytes(self) -> int:
        return self._data.content_bytes

    @property
    def created_at(self) -> datetime:
        return self._data.created_at

    @property
    def last_updated_at(self) -> datetime | None:
        return self._data.last_updated_at

    @property
    def optimization_progress_percent(self) -> int | None:
        """How far the index's background optimization has progressed, while one runs.

        Only a read of one index reports it; an index from a listing always has ``None``.
        """
        return self._data.optimization_progress_percent

    def __eq__(self, other: object) -> bool:
        return type(other) is type(self) and self._data == other._data

    def __hash__(self) -> int:
        return hash((type(self), self._data))

    def __repr__(self) -> str:
        return (
            f"<{type(self).__name__} {self.ref} state={self.state} documents={self.document_count}>"
        )
