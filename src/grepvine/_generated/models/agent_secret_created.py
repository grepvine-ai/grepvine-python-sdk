from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from uuid import UUID
import datetime


T = TypeVar("T", bound="AgentSecretCreated")


@_attrs_define
class AgentSecretCreated:
    """A new agent secret, which is shown only this once.

    Attributes:
        id (UUID):
        prefix (str): The first characters of the secret, shown to tell secrets apart.
        created_at (datetime.datetime):
        secret (str): The secret. It is shown only in this response.
        created_by (str): A name: of an account, an organization or an agent. Accounts and organizations share one
            namespace; an agent's name is unique within its organization. A name keeps the case it was created with, and any
            spelling that differs only in case refers to it; nothing else in the same namespace can take such a spelling.
        expires_at (datetime.datetime): When the secret stops working. Omitted when it never expires.
        last_used_at (datetime.datetime): When the agent last signed in with it. Omitted if it never has.
    """

    id: UUID
    prefix: str
    created_at: datetime.datetime
    secret: str
    created_by: str | None = None
    expires_at: datetime.datetime | None = None
    last_used_at: datetime.datetime | None = None
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)
        prefix = self.prefix
        created_at = self.created_at.isoformat()
        secret = self.secret
        _created_by_value = UNSET if self.created_by is None else self.created_by
        created_by = _created_by_value
        _expires_at_value = UNSET if self.expires_at is None else self.expires_at
        expires_at: str | Unset = UNSET
        if not isinstance(_expires_at_value, Unset):
            expires_at = _expires_at_value.isoformat()
        _last_used_at_value = UNSET if self.last_used_at is None else self.last_used_at
        last_used_at: str | Unset = UNSET
        if not isinstance(_last_used_at_value, Unset):
            last_used_at = _last_used_at_value.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "prefix": prefix,
                "created_at": created_at,
                "secret": secret,
            }
        )
        if created_by is not UNSET:
            field_dict["created_by"] = created_by
        if expires_at is not UNSET:
            field_dict["expires_at"] = expires_at
        if last_used_at is not UNSET:
            field_dict["last_used_at"] = last_used_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = UUID(d.pop("id"))

        prefix = d.pop("prefix")

        created_at = datetime.datetime.fromisoformat(d.pop("created_at"))

        secret = d.pop("secret")

        created_by = d.pop("created_by", UNSET)

        _expires_at = d.pop("expires_at", UNSET)
        expires_at: datetime.datetime | Unset
        if isinstance(_expires_at, Unset):
            expires_at = UNSET
        else:
            expires_at = datetime.datetime.fromisoformat(_expires_at)

        _last_used_at = d.pop("last_used_at", UNSET)
        last_used_at: datetime.datetime | Unset
        if isinstance(_last_used_at, Unset):
            last_used_at = UNSET
        else:
            last_used_at = datetime.datetime.fromisoformat(_last_used_at)

        agent_secret_created = cls(
            id=id,
            prefix=prefix,
            created_at=created_at,
            secret=secret,
            created_by=(None if isinstance(created_by, Unset) else created_by),
            expires_at=(None if isinstance(expires_at, Unset) else expires_at),
            last_used_at=(None if isinstance(last_used_at, Unset) else last_used_at),
        )

        agent_secret_created.additional_properties = d
        return agent_secret_created

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
