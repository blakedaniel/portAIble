"""Use case: run the SourceAnalyzer over an extracted session and store the draft profile."""

from __future__ import annotations

from dataclasses import dataclass

from ..config import settings
from ..domain import Session, SessionStatus
from ..ports import SessionRepositoryPort, SourceAnalyzerPort


@dataclass
class AnalyzeSourceUseCase:
    sessions: SessionRepositoryPort
    analyzer: SourceAnalyzerPort

    async def execute(self, session_id: str) -> Session:
        session = await self._require(session_id)
        if session.status not in (SessionStatus.EXTRACTED, SessionStatus.ANALYZED):
            raise ValueError(
                f"cannot analyze session in status {session.status.value!r}; "
                "extraction must complete first"
            )
        src_dir = settings.session_dir(session_id) / "src"
        profile = await self.analyzer.analyze(source_dir=src_dir)
        profile.analyzer_draft = True
        session.source_profile = profile
        session.transition(SessionStatus.ANALYZED)
        await self.sessions.save(session)
        return session

    async def _require(self, session_id: str) -> Session:
        session = await self.sessions.get(session_id)
        if session is None:
            raise LookupError(f"session {session_id} not found")
        return session
