"""JobRegistry — spawns background asyncio tasks that report progress through the DB.

Each background job:
  1. Creates a JobRow via the JobRepositoryPort (PENDING).
  2. Spawns asyncio.create_task running an inner coroutine.
  3. Inner coroutine opens its own AsyncSession (the request-scoped one is gone),
     marks RUNNING, calls the use case, marks COMPLETED or FAILED.

Survives restart in the sense that COMPLETED/FAILED records persist; in-flight
PENDING/RUNNING tasks are lost on process death (acceptable v1 — see plan).
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable

from ..infrastructure.db import session_scope
from ..infrastructure.repos.sqlite_job_repo import SqliteJobRepository
from ..ports import Job, JobKind, JobStatus

logger = logging.getLogger(__name__)


JobBody = Callable[[Callable[[int, str], Awaitable[None]]], Awaitable[None]]
"""A job body coroutine — receives an `on_progress(percent, message)` callback."""


class JobRegistry:
    """Spawns background jobs and persists their lifecycle through SQLite."""

    async def submit(
        self,
        *,
        session_id: str,
        kind: JobKind,
        body: JobBody,
    ) -> Job:
        """Create a Job row and schedule *body* to run in the background."""
        async with session_scope() as db:
            repo = SqliteJobRepository(db)
            job = await repo.create(session_id=session_id, kind=kind)

        # Detach from the request lifecycle.
        asyncio.create_task(self._run(job.id, body))
        return job

    async def _run(self, job_id: str, body: JobBody) -> None:
        async with session_scope() as db:
            repo = SqliteJobRepository(db)
            await repo.update(job_id, status=JobStatus.RUNNING, progress_message="starting...")

        async def on_progress(pct: int, msg: str) -> None:
            async with session_scope() as db:
                repo = SqliteJobRepository(db)
                await repo.update(job_id, progress_percentage=pct, progress_message=msg)

        try:
            await body(on_progress)
        except Exception as e:
            logger.exception("[job %s] failed", job_id)
            async with session_scope() as db:
                repo = SqliteJobRepository(db)
                await repo.update(
                    job_id, status=JobStatus.FAILED, error=f"{type(e).__name__}: {e}",
                )
            return

        async with session_scope() as db:
            repo = SqliteJobRepository(db)
            await repo.update(
                job_id, status=JobStatus.COMPLETED, progress_percentage=100,
                progress_message="done",
            )
