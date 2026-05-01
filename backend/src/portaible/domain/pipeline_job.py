"""Pipeline job — mirror of local-chat-agent's job status, kept locally for proxy polling."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel


class PipelineJobStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class PipelineJob(BaseModel):
    remote_job_id: str
    status: PipelineJobStatus = PipelineJobStatus.PENDING
    progress_percentage: int = 0
    progress_message: str = ""
    error: str | None = None
    result_path: str | None = None
