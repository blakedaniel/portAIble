"""Use cases: read/replace/confirm source and destination profiles."""

from __future__ import annotations

from dataclasses import dataclass

from ..domain import (
    DestinationProfile,
    Session,
    SessionStatus,
    SourceProfile,
)
from ..ports import SessionRepositoryPort, SourceAnalyzerPort


@dataclass
class UpdateSourceProfileUseCase:
    sessions: SessionRepositoryPort

    async def execute(self, session_id: str, profile: SourceProfile) -> Session:
        session = await _require(self.sessions, session_id)
        profile.analyzer_draft = False
        session.source_profile = profile
        await self.sessions.save(session)
        return session


@dataclass
class ConfirmSourceProfileUseCase:
    sessions: SessionRepositoryPort

    async def execute(self, session_id: str) -> Session:
        session = await _require(self.sessions, session_id)
        if session.source_profile is None:
            raise ValueError("no source profile to confirm")
        session.source_profile.analyzer_draft = False
        session.transition(SessionStatus.SOURCE_PROFILE_CONFIRMED)
        await self.sessions.save(session)
        return session


@dataclass
class SuggestDestinationUseCase:
    sessions: SessionRepositoryPort
    analyzer: SourceAnalyzerPort

    async def execute(self, session_id: str, target_hint: str | None) -> Session:
        session = await _require(self.sessions, session_id)
        if session.source_profile is None:
            raise ValueError("source profile must exist before destination suggestion")
        suggestion = await self.analyzer.suggest_destination(
            source_profile=session.source_profile,
            target_hint=target_hint,
        )
        suggestion.analyzer_draft = True
        session.destination_profile = suggestion
        await self.sessions.save(session)
        return session


@dataclass
class UpdateDestinationProfileUseCase:
    sessions: SessionRepositoryPort

    async def execute(self, session_id: str, profile: DestinationProfile) -> Session:
        session = await _require(self.sessions, session_id)
        profile.analyzer_draft = False
        session.destination_profile = profile
        await self.sessions.save(session)
        return session


@dataclass
class ConfirmDestinationProfileUseCase:
    sessions: SessionRepositoryPort

    async def execute(self, session_id: str) -> Session:
        session = await _require(self.sessions, session_id)
        if session.destination_profile is None:
            raise ValueError("no destination profile to confirm")
        session.destination_profile.analyzer_draft = False
        session.transition(SessionStatus.DESTINATION_PROFILE_CONFIRMED)
        await self.sessions.save(session)
        return session


async def _require(sessions: SessionRepositoryPort, session_id: str) -> Session:
    session = await sessions.get(session_id)
    if session is None:
        raise LookupError(f"session {session_id} not found")
    return session
