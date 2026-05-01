"""Use case: create a new Session with a fresh ID."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from ..domain import Session
from ..ports import SessionRepositoryPort


@dataclass
class CreateSessionUseCase:
    sessions: SessionRepositoryPort

    async def execute(self) -> Session:
        session = Session(id=uuid.uuid4().hex[:12])
        await self.sessions.save(session)
        return session
