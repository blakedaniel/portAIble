"""SQLite (async SQLAlchemy) implementation of SessionRepositoryPort."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...domain import (
    AssembledPrompt,
    DecisionAnswer,
    DesignDecision,
    DestinationProfile,
    ExtractionKind,
    Session,
    SessionStatus,
    SourceProfile,
)
from ...ports import SessionRepositoryPort, SessionSummary
from ..db.models import SessionRow


def _row_to_domain(row: SessionRow) -> Session:
    return Session(
        id=row.id,
        status=SessionStatus(row.status),
        created_at=row.created_at,
        updated_at=row.updated_at,
        extraction_kind=ExtractionKind(row.extraction_kind) if row.extraction_kind else None,
        source_uri=row.source_uri,
        extracted_file_count=row.extracted_file_count,
        source_profile=SourceProfile.model_validate(row.source_profile) if row.source_profile else None,
        destination_profile=DestinationProfile.model_validate(row.destination_profile) if row.destination_profile else None,
        design_decisions=[DesignDecision.model_validate(d) for d in (row.design_decisions or [])],
        decision_answers=[DecisionAnswer.model_validate(a) for a in (row.decision_answers or [])],
        assembled_prompt=AssembledPrompt.model_validate(row.assembled_prompt) if row.assembled_prompt else None,
        pipeline_remote_job_id=row.pipeline_remote_job_id,
        pipeline_result_path=row.pipeline_result_path,
    )


def _domain_to_row_kwargs(session: Session) -> dict:
    return {
        "id": session.id,
        "status": session.status.value,
        "created_at": session.created_at,
        "updated_at": session.updated_at,
        "extraction_kind": session.extraction_kind.value if session.extraction_kind else None,
        "source_uri": session.source_uri,
        "extracted_file_count": session.extracted_file_count,
        "source_profile": session.source_profile.model_dump(mode="json") if session.source_profile else None,
        "destination_profile": session.destination_profile.model_dump(mode="json") if session.destination_profile else None,
        "design_decisions": [d.model_dump(mode="json") for d in session.design_decisions] or None,
        "decision_answers": [a.model_dump(mode="json") for a in session.decision_answers] or None,
        "assembled_prompt": session.assembled_prompt.model_dump(mode="json") if session.assembled_prompt else None,
        "pipeline_remote_job_id": session.pipeline_remote_job_id,
        "pipeline_result_path": session.pipeline_result_path,
    }


class SqliteSessionRepository(SessionRepositoryPort):
    def __init__(self, session: AsyncSession):
        self._db = session

    async def get(self, session_id: str) -> Session | None:
        row = await self._db.get(SessionRow, session_id)
        return _row_to_domain(row) if row else None

    async def save(self, session: Session) -> None:
        existing = await self._db.get(SessionRow, session.id)
        kwargs = _domain_to_row_kwargs(session)
        if existing is None:
            self._db.add(SessionRow(**kwargs))
        else:
            for k, v in kwargs.items():
                setattr(existing, k, v)
        await self._db.flush()

    async def list(self) -> list[SessionSummary]:
        result = await self._db.execute(
            select(SessionRow.id, SessionRow.status, SessionRow.created_at, SessionRow.updated_at)
            .order_by(SessionRow.updated_at.desc())
        )
        return [
            SessionSummary(id=r.id, status=r.status, created_at=r.created_at, updated_at=r.updated_at)
            for r in result.all()
        ]

    async def delete(self, session_id: str) -> None:
        row = await self._db.get(SessionRow, session_id)
        if row is not None:
            await self._db.delete(row)
            await self._db.flush()
