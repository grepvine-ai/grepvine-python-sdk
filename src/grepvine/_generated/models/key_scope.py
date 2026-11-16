from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..models.permission import Permission
from typing import cast
import datetime


T = TypeVar("T", bound="KeyScope")


@_attrs_define
class KeyScope:
    """What a key reaches and may do. A field left out sets no limit; the expiry is always given.

    Attributes:
        permissions (list[Permission]): The permissions a key carries, each named once.
        expires_at (datetime.datetime | None): When the key stops working, at most one year ahead, or null for a key
            that never expires.
        agent (str): A name: of an account, an organization or an agent. Accounts and organizations share one namespace;
            an agent's name is unique within its organization. A name keeps the case it was created with, and any spelling
            that differs only in case refers to it; nothing else in the same namespace can take such a spelling.
        organization (str): A name: of an account, an organization or an agent. Accounts and organizations share one
            namespace; an agent's name is unique within its organization. A name keeps the case it was created with, and any
            spelling that differs only in case refers to it; nothing else in the same namespace can take such a spelling.
        indexes (list[str]): The indexes a key reaches, by name, in the key's one organization. Omitted for every index
            of its organizations, including indexes created later. A request names at least one; a key's list is empty once
            every index it named is deleted.
    """

    permissions: list[Permission]
    expires_at: datetime.datetime | None
    agent: str | None = None
    organization: str | None = None
    indexes: list[str] = _attrs_field(factory=list)

    def to_dict(self) -> dict[str, Any]:
        permissions = []
        for componentsschemas_permissions_item_data in self.permissions:
            componentsschemas_permissions_item = componentsschemas_permissions_item_data.value
            permissions.append(componentsschemas_permissions_item)

        expires_at: None | str
        if isinstance(self.expires_at, datetime.datetime):
            expires_at = self.expires_at.isoformat()
        else:
            expires_at = self.expires_at
        _agent_value = UNSET if self.agent is None else self.agent
        agent = _agent_value
        _organization_value = UNSET if self.organization is None else self.organization
        organization = _organization_value
        _indexes_value = UNSET if not self.indexes else self.indexes
        indexes: list[str] | Unset = UNSET
        if not isinstance(_indexes_value, Unset):
            indexes = _indexes_value

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "permissions": permissions,
                "expires_at": expires_at,
            }
        )
        if agent is not UNSET:
            field_dict["agent"] = agent
        if organization is not UNSET:
            field_dict["organization"] = organization
        if indexes is not UNSET:
            field_dict["indexes"] = indexes

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        permissions = []
        _permissions = d.pop("permissions")
        for componentsschemas_permissions_item_data in _permissions:
            componentsschemas_permissions_item = Permission(componentsschemas_permissions_item_data)

            permissions.append(componentsschemas_permissions_item)

        def _parse_expires_at(data: object) -> datetime.datetime | None:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                expires_at_type_0 = datetime.datetime.fromisoformat(data)

                return expires_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None, data)

        expires_at = _parse_expires_at(d.pop("expires_at"))

        agent = d.pop("agent", UNSET)

        organization = d.pop("organization", UNSET)

        indexes = cast(list[str], d.pop("indexes", UNSET))

        key_scope = cls(
            permissions=permissions,
            expires_at=expires_at,
            agent=(None if isinstance(agent, Unset) else agent),
            organization=(None if isinstance(organization, Unset) else organization),
            indexes=([] if isinstance(indexes, Unset) else indexes),
        )

        return key_scope
