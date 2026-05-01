"""Session aggregate — single source of truth for a porting workflow run."""

from __future__ import annotations

import secrets
from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from .design_decision import DecisionAnswer, DesignDecision
from .destination_profile import DestinationProfile
from .pipeline_job import PipelineJob
from .prompt import AssembledPrompt
from .source_profile import SourceProfile


class SessionStatus(StrEnum):
    CREATED = "created"
    EXTRACTED = "extracted"
    ANALYZED = "analyzed"
    SOURCE_PROFILE_CONFIRMED = "source_profile_confirmed"
    DESTINATION_PROFILE_CONFIRMED = "destination_profile_confirmed"
    DECISIONS_ANSWERED = "decisions_answered"
    PROMPT_BUILT = "prompt_built"
    PIPELINE_SUBMITTED = "pipeline_submitted"
    PIPELINE_COMPLETED = "pipeline_completed"
    PIPELINE_FAILED = "pipeline_failed"


class ExtractionKind(StrEnum):
    ZIP = "zip"
    GITHUB_PUBLIC = "github_public"
    GITHUB_PRIVATE = "github_private"


class IllegalTransitionError(ValueError):
    """Raised when Session.advance_to() is called with a status unreachable from the current one."""


_FORWARD_TRANSITIONS: dict[SessionStatus, set[SessionStatus]] = {
    SessionStatus.CREATED: {SessionStatus.EXTRACTED},
    # Re-extraction or re-analysis allowed for idempotent retries
    SessionStatus.EXTRACTED: {SessionStatus.ANALYZED, SessionStatus.EXTRACTED},
    SessionStatus.ANALYZED: {
        SessionStatus.SOURCE_PROFILE_CONFIRMED,
        SessionStatus.ANALYZED,
    },
    SessionStatus.SOURCE_PROFILE_CONFIRMED: {
        SessionStatus.DESTINATION_PROFILE_CONFIRMED,
        SessionStatus.SOURCE_PROFILE_CONFIRMED,
    },
    SessionStatus.DESTINATION_PROFILE_CONFIRMED: {
        SessionStatus.DECISIONS_ANSWERED,
        SessionStatus.DESTINATION_PROFILE_CONFIRMED,
        SessionStatus.PROMPT_BUILT,  # decisions can be skipped
    },
    SessionStatus.DECISIONS_ANSWERED: {
        SessionStatus.PROMPT_BUILT,
        SessionStatus.DECISIONS_ANSWERED,
    },
    SessionStatus.PROMPT_BUILT: {
        SessionStatus.PIPELINE_SUBMITTED,
        SessionStatus.PROMPT_BUILT,
    },
    SessionStatus.PIPELINE_SUBMITTED: {
        SessionStatus.PIPELINE_COMPLETED,
        SessionStatus.PIPELINE_FAILED,
    },
    SessionStatus.PIPELINE_COMPLETED: set(),
    SessionStatus.PIPELINE_FAILED: {SessionStatus.PIPELINE_SUBMITTED},
}


def new_session_id() -> str:
    """12-char hex id — matches local-chat-agent's job_id convention."""
    return secrets.token_hex(6)


def utcnow() -> datetime:
    return datetime.now(UTC)


class Session(BaseModel):
    id: str = Field(default_factory=new_session_id)
    status: SessionStatus = SessionStatus.CREATED
    extraction_kind: ExtractionKind | None = None
    source_uri: str | None = None
    extracted_file_count: int = 0
    source_profile: SourceProfile | None = None
    destination_profile: DestinationProfile | None = None
    design_decisions: list[DesignDecision] = Field(default_factory=list)
    decision_answers: list[DecisionAnswer] = Field(default_factory=list)
    assembled_prompt: AssembledPrompt | None = None
    pipeline_job: PipelineJob | None = None
    pipeline_remote_job_id: str | None = None
    pipeline_result_path: str | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    def transition(self, target: SessionStatus) -> None:
        """Validate and apply a status transition; raise on illegal moves."""
        if target == self.status:
            self.updated_at = utcnow()
            return
        allowed = _FORWARD_TRANSITIONS.get(self.status, set())
        if target not in allowed:
            raise IllegalTransitionError(
                f"illegal session transition: {self.status.value} -> {target.value}"
            )
        self.status = target
        self.updated_at = utcnow()

    # Back-compat alias retained while older use cases migrate.
    advance_to = transition
