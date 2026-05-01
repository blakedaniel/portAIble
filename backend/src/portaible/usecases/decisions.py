"""Use cases for the design decisions wizard."""

from __future__ import annotations

from dataclasses import dataclass

from ..domain import DecisionAnswer, DesignDecision, Session, SessionStatus
from ..ports import DesignDecisionsPort, SessionRepositoryPort


@dataclass
class GenerateDesignDecisionsUseCase:
    sessions: SessionRepositoryPort
    decisions: DesignDecisionsPort

    async def execute(self, session_id: str) -> list[DesignDecision]:
        session = await _require(self.sessions, session_id)
        if session.source_profile is None or session.destination_profile is None:
            raise ValueError(
                "both source and destination profiles must be confirmed before generating decisions"
            )
        # Optional: enforce that DESTINATION has been confirmed (analyzer_draft=False)
        if session.destination_profile.analyzer_draft:
            raise ValueError("destination profile must be confirmed before generating decisions")

        items = await self.decisions.generate(
            source=session.source_profile,
            destination=session.destination_profile,
        )
        # Stable assignment: replace any prior generation; this is idempotent.
        session.design_decisions = items
        # Don't transition here — only after answers are submitted.
        await self.sessions.save(session)
        return items


@dataclass
class SubmitDesignAnswersUseCase:
    sessions: SessionRepositoryPort

    async def execute(self, session_id: str, answers: list[DecisionAnswer]) -> Session:
        session = await _require(self.sessions, session_id)
        if not session.design_decisions:
            raise ValueError("no decisions have been generated for this session")

        # Validate every decision_id in answers maps to a real decision.
        decision_ids = {d.id for d in session.design_decisions}
        for a in answers:
            if a.decision_id not in decision_ids:
                raise ValueError(f"unknown decision id: {a.decision_id}")
        session.decision_answers = answers
        session.transition(SessionStatus.DECISIONS_ANSWERED)
        await self.sessions.save(session)
        return session


async def _require(sessions: SessionRepositoryPort, session_id: str) -> Session:
    session = await sessions.get(session_id)
    if session is None:
        raise LookupError(f"session {session_id} not found")
    return session
