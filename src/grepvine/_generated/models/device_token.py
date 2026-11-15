from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, TYPE_CHECKING

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..models.permission import Permission
from typing import cast
from uuid import UUID
import datetime

if TYPE_CHECKING:
    from ..models.agent_secret_created import AgentSecretCreated


T = TypeVar("T", bound="DeviceToken")


@_attrs_define
class DeviceToken:
    """What an approved device receives, once: an API key, with `key` and the key's fields, or a new agent secret in
    `agent_secret`. Exactly one of `key` and `agent_secret` is set.

        Attributes:
            id (UUID): The key's unique ID.
            name (str): The name the key was given.
            prefix (str): The first characters of the key, shown to tell keys apart.
            agent (str): A name: of an account, an organization or an agent. Accounts and organizations share one namespace;
                an agent's name is unique within its organization. A name keeps the case it was created with, and any spelling
                that differs only in case refers to it; nothing else in the same namespace can take such a spelling.
            organization (str): A name: of an account, an organization or an agent. Accounts and organizations share one
                namespace; an agent's name is unique within its organization. A name keeps the case it was created with, and any
                spelling that differs only in case refers to it; nothing else in the same namespace can take such a spelling.
            indexes (list[str]): The indexes a key reaches, by name, in the key's one organization. Omitted for every index
                of its organizations, including indexes created later. A request names at least one; a key's list is empty once
                every index it named is deleted.
            permissions (list[Permission]): What the key may do.
            created_at (datetime.datetime): When the key was created.
            expires_at (datetime.datetime): When the key stops working. Omitted when it never expires.
            key (str): The secret API key. It is shown only in this response; send it as `Authorization: Bearer <key>`.
            agent_secret (AgentSecretCreated): A new agent secret, which is shown only this once.
    """

    id: UUID | None = None
    name: str | None = None
    prefix: str | None = None
    agent: str | None = None
    organization: str | None = None
    indexes: list[str] = _attrs_field(factory=list)
    permissions: list[Permission] = _attrs_field(factory=list)
    created_at: datetime.datetime | None = None
    expires_at: datetime.datetime | None = None
    key: str | None = None
    agent_secret: AgentSecretCreated | None = None
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        _id_value = UNSET if self.id is None else self.id
        id: str | Unset = UNSET
        if not isinstance(_id_value, Unset):
            id = str(_id_value)
        _name_value = UNSET if self.name is None else self.name
        name = _name_value
        _prefix_value = UNSET if self.prefix is None else self.prefix
        prefix = _prefix_value
        _agent_value = UNSET if self.agent is None else self.agent
        agent = _agent_value
        _organization_value = UNSET if self.organization is None else self.organization
        organization = _organization_value
        _indexes_value = UNSET if self.indexes is None else self.indexes
        indexes: list[str] | Unset = UNSET
        if not isinstance(_indexes_value, Unset):
            indexes = _indexes_value

        _permissions_value = UNSET if self.permissions is None else self.permissions
        permissions: list[str] | Unset = UNSET
        if not isinstance(_permissions_value, Unset):
            permissions = []
            for permissions_item_data in _permissions_value:
                permissions_item = permissions_item_data.value
                permissions.append(permissions_item)

        _created_at_value = UNSET if self.created_at is None else self.created_at
        created_at: str | Unset = UNSET
        if not isinstance(_created_at_value, Unset):
            created_at = _created_at_value.isoformat()
        _expires_at_value = UNSET if self.expires_at is None else self.expires_at
        expires_at: str | Unset = UNSET
        if not isinstance(_expires_at_value, Unset):
            expires_at = _expires_at_value.isoformat()
        _key_value = UNSET if self.key is None else self.key
        key = _key_value
        _agent_secret_value = UNSET if self.agent_secret is None else self.agent_secret
        agent_secret: dict[str, Any] | Unset = UNSET
        if not isinstance(_agent_secret_value, Unset):
            agent_secret = _agent_secret_value.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if name is not UNSET:
            field_dict["name"] = name
        if prefix is not UNSET:
            field_dict["prefix"] = prefix
        if agent is not UNSET:
            field_dict["agent"] = agent
        if organization is not UNSET:
            field_dict["organization"] = organization
        if indexes is not UNSET:
            field_dict["indexes"] = indexes
        if permissions is not UNSET:
            field_dict["permissions"] = permissions
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if expires_at is not UNSET:
            field_dict["expires_at"] = expires_at
        if key is not UNSET:
            field_dict["key"] = key
        if agent_secret is not UNSET:
            field_dict["agent_secret"] = agent_secret

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.agent_secret_created import AgentSecretCreated  # noqa: PLC0415

        d = dict(src_dict)
        _id = d.pop("id", UNSET)
        id: UUID | Unset
        if isinstance(_id, Unset):
            id = UNSET
        else:
            id = UUID(_id)

        name = d.pop("name", UNSET)

        prefix = d.pop("prefix", UNSET)

        agent = d.pop("agent", UNSET)

        organization = d.pop("organization", UNSET)

        indexes = cast(list[str], d.pop("indexes", UNSET))

        _permissions = d.pop("permissions", UNSET)
        permissions: list[Permission] | Unset = UNSET
        if _permissions is not UNSET:
            permissions = []
            for permissions_item_data in _permissions:
                permissions_item = Permission(permissions_item_data)

                permissions.append(permissions_item)

        _created_at = d.pop("created_at", UNSET)
        created_at: datetime.datetime | Unset
        if isinstance(_created_at, Unset):
            created_at = UNSET
        else:
            created_at = datetime.datetime.fromisoformat(_created_at)

        _expires_at = d.pop("expires_at", UNSET)
        expires_at: datetime.datetime | Unset
        if isinstance(_expires_at, Unset):
            expires_at = UNSET
        else:
            expires_at = datetime.datetime.fromisoformat(_expires_at)

        key = d.pop("key", UNSET)

        _agent_secret = d.pop("agent_secret", UNSET)
        agent_secret: AgentSecretCreated | Unset
        if isinstance(_agent_secret, Unset):
            agent_secret = UNSET
        else:
            agent_secret = AgentSecretCreated.from_dict(_agent_secret)

        device_token = cls(
            id=(None if isinstance(id, Unset) else id),
            name=(None if isinstance(name, Unset) else name),
            prefix=(None if isinstance(prefix, Unset) else prefix),
            agent=(None if isinstance(agent, Unset) else agent),
            organization=(None if isinstance(organization, Unset) else organization),
            indexes=([] if isinstance(indexes, Unset) else indexes),
            permissions=([] if isinstance(permissions, Unset) else permissions),
            created_at=(None if isinstance(created_at, Unset) else created_at),
            expires_at=(None if isinstance(expires_at, Unset) else expires_at),
            key=(None if isinstance(key, Unset) else key),
            agent_secret=(None if isinstance(agent_secret, Unset) else agent_secret),
        )

        device_token.additional_properties = d
        return device_token

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
