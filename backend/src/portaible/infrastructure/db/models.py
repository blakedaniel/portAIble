"""SQLAlchemy ORM models — flat tables with JSON columns for rich Pydantic shapes."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import JSON, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


def _now() -> datetime:
    return datetime.now(UTC)


class SessionRow(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(12), primary_key=True)
    status: Mapped[str] = mapped_column(String(48), nullable=False, default="created")
    created_at: Mapped[datetime] = mapped_column(default=_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(default=_now, onupdate=_now, nullable=False)

    extraction_kind: Mapped[str | None] = mapped_column(String(32), nullable=True)
    source_uri: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    extracted_file_count: Mapped[int] = mapped_column(default=0, nullable=False)

    # Pydantic-shaped blobs persisted as JSON. Keeps the schema flat while preserving rich shape.
    source_profile: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    destination_profile: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    design_decisions: Mapped[list | None] = mapped_column(JSON, nullable=True)
    decision_answers: Mapped[list | None] = mapped_column(JSON, nullable=True)
    assembled_prompt: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    pipeline_remote_job_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    pipeline_result_path: Mapped[str | None] = mapped_column(String(2048), nullable=True)

    jobs: Mapped[list[JobRow]] = relationship(back_populates="session", cascade="all, delete-orphan")

    __table_args__ = (Index("ix_sessions_updated_at", "updated_at"),)


class JobRow(Base):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String(12), primary_key=True)
    session_id: Mapped[str] = mapped_column(
        String(12),
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")
    progress_percentage: Mapped[int] = mapped_column(default=0, nullable=False)
    progress_message: Mapped[str] = mapped_column(String(512), default="", nullable=False)
    error: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(default=_now, onupdate=_now, nullable=False)

    session: Mapped[SessionRow] = relationship(back_populates="jobs")

    __table_args__ = (Index("ix_jobs_session_id", "session_id"),)
