"""Port: persist background-job state (analyzer, suggest, decisions, github extract)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel


class JobKind(StrEnum):
    ANALYZE = "analyze"
    SUGGEST_DESTINATION = "suggest_destination"
    GENERATE_DECISIONS = "generate_decisions"
    EXTRACT_GITHUB = "extract_github"


class JobStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Job(BaseModel):
    id: str
    session_id: str
    kind: JobKind
    status: JobStatus = JobStatus.PENDING
    progress_percentage: int = 0
    progress_message: str = ""
    error: str | None = None
    created_at: datetime
    updated_at: datetime


class JobRepositoryPort(ABC):
    @abstractmethod
    async def create(self, *, session_id: str, kind: JobKind) -> Job: ...

    @abstractmethod
    async def get(self, job_id: str) -> Job | None: ...

    @abstractmethod
    async def update(
        self,
        job_id: str,
        *,
        status: JobStatus | None = None,
        progress_percentage: int | None = None,
        progress_message: str | None = None,
        error: str | None = None,
    ) -> Job: ...

    @abstractmethod
    async def list_for_session(self, session_id: str) -> list[Job]: ...
