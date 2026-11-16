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


T = TypeVar("T", bound="DeviceAuthorizationRequest")


@_attrs_define
class DeviceAuthorizationRequest:
    """Starts a device authorization. The scope fields are what the device asks for; the person approving it sees them and
    may change them. A scope field left out sets no limit. A request for an API key names it, its permissions and its
    expiry (`expires_at`, null for never); a request for an agent secret sends `agent_secret` and none of the other
    fields.

        Attributes:
            agent_secret (DeviceAgentSecret): A new secret of an agent, which a device asks for instead of an API key.
            api_key_name (str): The name to give the API key the device receives, 1 to 128 characters. Required for an API
                key.
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
            expires_at (datetime.datetime | None): When the key stops working, at most one year ahead, or null for a key
                that never expires.
    """

    agent_secret: DeviceAgentSecret | None = None
    api_key_name: str | None = None
    agent: str | None = None
    organization: str | None = None
    indexes: list[str] = _attrs_field(factory=list)
    permissions: list[Permission] = _attrs_field(factory=list)
    expires_at: datetime.datetime | None | None = None

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
        _indexes_value = UNSET if self.indexes is None else self.indexes
        indexes: list[str] | Unset = UNSET
        if not isinstance(_indexes_value, Unset):
            indexes = _indexes_value

        _permissions_value = UNSET if self.permissions is None else self.permissions
        permissions: list[str] | Unset = UNSET
        if not isinstance(_permissions_value, Unset):
            permissions = []
            for componentsschemas_permissions_item_data in _permissions_value:
                componentsschemas_permissions_item = componentsschemas_permissions_item_data.value
                permissions.append(componentsschemas_permissions_item)

        _expires_at_value = UNSET if self.expires_at is None else self.expires_at
        expires_at: None | str | Unset
        if isinstance(_expires_at_value, Unset):
            expires_at = UNSET
        elif isinstance(_expires_at_value, datetime.datetime):
            expires_at = _expires_at_value.isoformat()
        else:
            expires_at = _expires_at_value

        field_dict: dict[str, Any] = {}

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

        def _parse_expires_at(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                expires_at_type_0 = datetime.datetime.fromisoformat(data)

                return expires_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        expires_at = _parse_expires_at(d.pop("expires_at", UNSET))

        device_authorization_request = cls(
            agent_secret=(None if isinstance(agent_secret, Unset) else agent_secret),
            api_key_name=(None if isinstance(api_key_name, Unset) else api_key_name),
            agent=(None if isinstance(agent, Unset) else agent),
            organization=(None if isinstance(organization, Unset) else organization),
            indexes=([] if isinstance(indexes, Unset) else indexes),
            permissions=([] if isinstance(permissions, Unset) else permissions),
            expires_at=(None if isinstance(expires_at, Unset) else expires_at),
        )

        return device_authorization_request
