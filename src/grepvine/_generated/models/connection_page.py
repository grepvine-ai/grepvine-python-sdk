from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, TYPE_CHECKING

from attrs import define as _attrs_define


if TYPE_CHECKING:
    from ..models.connection import Connection


T = TypeVar("T", bound="ConnectionPage")


@_attrs_define
class ConnectionPage:
    """The account's connections.

    Attributes:
        connections (list[Connection]):
    """

    connections: list[Connection]

    def to_dict(self) -> dict[str, Any]:
        connections = []
        for connections_item_data in self.connections:
            connections_item = connections_item_data.to_dict()
            connections.append(connections_item)

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "connections": connections,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.connection import Connection  # noqa: PLC0415

        d = dict(src_dict)
        connections = []
        _connections = d.pop("connections")
        for connections_item_data in _connections:
            connections_item = Connection.from_dict(connections_item_data)

            connections.append(connections_item)

        connection_page = cls(
            connections=connections,
        )

        return connection_page
