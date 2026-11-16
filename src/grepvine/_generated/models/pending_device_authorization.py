from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, TYPE_CHECKING

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..models.permission import Permission
from typing import cast
import datetime

if TYPE_CHECKING:
    from ..models.device_agent_secret import DeviceAgentSecret


T = TypeVar("T", bound="PendingDeviceAuthorization")


@_attrs_define
class PendingDeviceAuthorization:
    """What a pending device authorization asks for. A request for an agent secret has `agent_secret` and none of the key's
    fields.

        Attributes:
            agent_secret (DeviceAgentSecret): A new secret of an agent, which a device asks for instead of an API key.
            api_key_name (str): The name the key the device receives will have.
            agent (str): A name: of an account, an organization or an agent. Accounts and organizations share one namespace;
                an agent's name is unique within its organization. A name keeps the case it was created with, and any spelling
                that differs only in case refers to it; nothing else in the same namespace can take such a spelling.
            organization (str): A name: of an account, an organization or an agent. Accounts and organizations share one
                namespace; an agent's name is unique within its organization. A name keeps the case it was created with, and any
                spelling that differs only in case refers to it; nothing else in the same namespace can take such a spelling.
            indexes (list[str]): The indexes a key reaches, by name, in the key's one organization. Omitted for every index
                of its organizations, including indexes created later. A request names at least one; a key's list is empty once
                every index it named is deleted.
            permissions (list[Permission]): The permissions a key carries, each named once.
            expires_at (datetime.datetime): When the key the device receives stops working. Omitted when it never expires.
    """

    agent_secret: DeviceAgentSecret | None = None
    api_key_name: str | None = None
    agent: str | None = None
    organization: str | None = None
    indexes: list[str] = _attrs_field(factory=list)
    permissions: list[Permission] = _attrs_field(factory=list)
    expires_at: datetime.datetime | None = None
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        _agent_secret_value = UNSET if self.agent_secret is None else self.agent_secret
        agent_secret: dict[str, Any] | Unset = UNSET
        if not isinstance(_agent_secret_value, Unset):
            agent_secret = _agent_secret_value.to_dict()
        _api_key_name_value = UNSET if self.api_key_name is None else self.api_key_name
        api_key_name = _api_key_name_value
        _agent_value = UNSET if self.agent is None else self.agent
        agent = _agent_value
        _organization_value = UNSET if self.organization is None else self.organization
        organization = _organization_value
        _indexes_value = UNSET if not self.indexes else self.indexes
        indexes: list[str] | Unset = UNSET
        if not isinstance(_indexes_value, Unset):
            indexes = _indexes_value

        _permissions_value = UNSET if not self.permissions else self.permissions
        permissions: list[str] | Unset = UNSET
        if not isinstance(_permissions_value, Unset):
            permissions = []
            for componentsschemas_permissions_item_data in _permissions_value:
                componentsschemas_permissions_item = componentsschemas_permissions_item_data.value
                permissions.append(componentsschemas_permissions_item)

        _expires_at_value = UNSET if self.expires_at is None else self.expires_at
        expires_at: str | Unset = UNSET
        if not isinstance(_expires_at_value, Unset):
            expires_at = _expires_at_value.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if agent_secret is not UNSET:
            field_dict["agent_secret"] = agent_secret
        if api_key_name is not UNSET:
            field_dict["api_key_name"] = api_key_name
        if agent is not UNSET:
            field_dict["agent"] = agent
        if organization is not UNSET:
            field_dict["organization"] = organization
        if indexes is not UNSET:
            field_dict["indexes"] = indexes
        if permissions is not UNSET:
            field_dict["permissions"] = permissions
        if expires_at is not UNSET:
            field_dict["expires_at"] = expires_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.device_agent_secret import DeviceAgentSecret  # noqa: PLC0415

        d = dict(src_dict)
        _agent_secret = d.pop("agent_secret", UNSET)
        agent_secret: DeviceAgentSecret | Unset
        if isinstance(_agent_secret, Unset):
            agent_secret = UNSET
        else:
            agent_secret = DeviceAgentSecret.from_dict(_agent_secret)

        api_key_name = d.pop("api_key_name", UNSET)

        agent = d.pop("agent", UNSET)

        organization = d.pop("organization", UNSET)

        indexes = cast(list[str], d.pop("indexes", UNSET))

        _permissions = d.pop("permissions", UNSET)
        permissions: list[Permission] | Unset = UNSET
        if _permissions is not UNSET:
            permissions = []
            for componentsschemas_permissions_item_data in _permissions:
                componentsschemas_permissions_item = Permission(
                    componentsschemas_permissions_item_data
                )

                permissions.append(componentsschemas_permissions_item)

        _expires_at = d.pop("expires_at", UNSET)
        expires_at: datetime.datetime | Unset
        if isinstance(_expires_at, Unset):
            expires_at = UNSET
        else:
            expires_at = datetime.datetime.fromisoformat(_expires_at)

        pending_device_authorization = cls(
            agent_secret=(None if isinstance(agent_secret, Unset) else agent_secret),
            api_key_name=(None if isinstance(api_key_name, Unset) else api_key_name),
            agent=(None if isinstance(agent, Unset) else agent),
            organization=(None if isinstance(organization, Unset) else organization),
            indexes=([] if isinstance(indexes, Unset) else indexes),
            permissions=([] if isinstance(permissions, Unset) else permissions),
            expires_at=(None if isinstance(expires_at, Unset) else expires_at),
        )

        pending_device_authorization.additional_properties = d
        return pending_device_authorization

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
