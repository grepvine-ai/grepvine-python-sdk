"""Effect vocabulary shared by every operation.

An operation is a generator that yields an effect (call an API operation,
sleep, read the clock, report progress, or change the client's session) and
receives the effect's outcome. The synchronous and asynchronous clients each
interpret the effects in a small loop, so every operation is written once.

A :class:`Call` names one module of the private ``_generated.api`` package.
The synchronous client runs its ``sync_detailed`` function and the
asynchronous client its ``asyncio_detailed`` function. Errors the service
answers with are raised into the operation as :class:`~grepvine.APIError`.
"""

from __future__ import annotations

from collections.abc import Callable, Generator, Mapping
from dataclasses import dataclass, field
from types import ModuleType
from typing import Any, TypeAlias, TypeVar

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class Session:
    """A signed-in user session: its cookie and the token state changes must carry."""

    cookie_name: str
    cookie: str
    csrf_token: str


@dataclass(frozen=True, slots=True)
class Call:
    """Run one API operation and receive its response.

    ``auth`` is False for the operations that need no credentials, such as
    signing in or starting a device login.
    """

    operation: ModuleType
    args: tuple[Any, ...] = ()
    kwargs: Mapping[str, Any] = field(default_factory=dict)
    auth: bool = True

    @property
    def name(self) -> str:
        return self.operation.__name__.rsplit(".", 1)[-1]


@dataclass(frozen=True, slots=True)
class Sleep:
    """Sleep before the next step of this operation."""

    seconds: float


@dataclass(frozen=True, slots=True)
class Now:
    """Read the client's monotonic clock."""


@dataclass(frozen=True, slots=True)
class Notify:
    """Call a function of the caller's; an asynchronous client awaits its result if needed."""

    callback: Callable[[Any], Any]
    value: Any


@dataclass(frozen=True, slots=True)
class SetSession:
    """Make the client use this session, or no session, for its later requests."""

    session: Session | None


Effect: TypeAlias = Call | Sleep | Now | Notify | SetSession
Op: TypeAlias = Generator[Effect, Any, T]
