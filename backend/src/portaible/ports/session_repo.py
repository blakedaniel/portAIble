"""SessionRepositoryPort — persistence boundary for the Session aggregate."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

from ..domain import Session


@dataclass(frozen=True)
class SessionSummary:
    id: str
    status: str
    created_at: datetime
    updated_at: datetime


class SessionRepositoryPort(ABC):
    @abstractmethod
    async def get(self, session_id: str) -> Session | None: ...

    @abstractmethod
    async def save(self, session: Session) -> None: ...

    @abstractmethod
    async def list(self) -> list[SessionSummary]: ...

    @abstractmethod
    async def delete(self, session_id: str) -> None: ...
