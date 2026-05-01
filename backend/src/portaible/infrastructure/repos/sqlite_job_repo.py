"""SQLite (async SQLAlchemy) implementation of JobRepositoryPort."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...ports import Job, JobKind, JobRepositoryPort, JobStatus
from ..db.models import JobRow


def _row_to_domain(row: JobRow) -> Job:
    return Job(
        id=row.id,
        session_id=row.session_id,
        kind=JobKind(row.kind),
        status=JobStatus(row.status),
        progress_percentage=row.progress_percentage,
        progress_message=row.progress_message,
        error=row.error,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class SqliteJobRepository(JobRepositoryPort):
    def __init__(self, session: AsyncSession):
        self._db = session

    async def create(self, *, session_id: str, kind: JobKind) -> Job:
        now = datetime.now(UTC)
        row = JobRow(
            id=uuid.uuid4().hex[:12],
            session_id=session_id,
            kind=kind.value,
            status=JobStatus.PENDING.value,
            created_at=now,
            updated_at=now,
        )
        self._db.add(row)
        await self._db.flush()
        return _row_to_domain(row)

    async def get(self, job_id: str) -> Job | None:
        row = await self._db.get(JobRow, job_id)
        return _row_to_domain(row) if row else None

    async def update(
        self,
        job_id: str,
        *,
        status: JobStatus | None = None,
        progress_percentage: int | None = None,
        progress_message: str | None = None,
        error: str | None = None,
    ) -> Job:
        row = await self._db.get(JobRow, job_id)
        if row is None:
            raise KeyError(f"job {job_id} not found")
        if status is not None:
            row.status = status.value
        if progress_percentage is not None:
            row.progress_percentage = progress_percentage
        if progress_message is not None:
            row.progress_message = progress_message
        if error is not None:
            row.error = error
        row.updated_at = datetime.now(UTC)
        await self._db.flush()
        return _row_to_domain(row)

    async def list_for_session(self, session_id: str) -> list[Job]:
        result = await self._db.execute(
            select(JobRow).where(JobRow.session_id == session_id).order_by(JobRow.created_at.desc())
        )
        return [_row_to_domain(r) for r in result.scalars().all()]
