"""Pydantic request/response DTOs at the HTTP boundary.

Re-exports domain shapes where the wire format matches; introduces dedicated
DTOs only when the API surface differs from the domain.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from ..domain import (
    AssembledPrompt,
    DecisionAnswer,
    DesignDecision,
    DestinationProfile,
    PipelineJob,
    Session,
    SourceProfile,
)
from ..ports import Job, SessionSummary

__all__ = [
    "AssembledPrompt",
    "DecisionAnswer",
    "DesignDecision",
    "DestinationProfile",
    "GithubExtractRequest",
    "JobDTO",
    "JobIdResponse",
    "PipelineJob",
    "Session",
    "SessionListResponse",
    "SourceProfile",
    "SuggestDestinationRequest",
]


class GithubExtractRequest(BaseModel):
    url: str
    ref: str | None = None
    pat: str | None = None
    kind: str = "public"  # "public" or "private"


class SuggestDestinationRequest(BaseModel):
    target_hint: str | None = None


class JobIdResponse(BaseModel):
    job_id: str


class JobDTO(BaseModel):
    id: str
    session_id: str
    kind: str
    status: str
    progress_percentage: int
    progress_message: str
    error: str | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_domain(cls, job: Job) -> "JobDTO":
        return cls(
            id=job.id,
            session_id=job.session_id,
            kind=job.kind.value,
            status=job.status.value,
            progress_percentage=job.progress_percentage,
            progress_message=job.progress_message,
            error=job.error,
            created_at=job.created_at,
            updated_at=job.updated_at,
        )


class SessionListResponse(BaseModel):
    sessions: list[dict]

    @classmethod
    def from_summaries(cls, summaries: list[SessionSummary]) -> "SessionListResponse":
        return cls(
            sessions=[
                {
                    "id": s.id,
                    "status": s.status,
                    "created_at": s.created_at.isoformat(),
                    "updated_at": s.updated_at.isoformat(),
                }
                for s in summaries
            ]
        )
