"""Use cases: submit/poll/fetch the AI Pipeline (local-chat-agent) for a session."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..config import settings
from ..domain import PipelineJob, PipelineJobStatus, Session, SessionStatus
from ..ports import AIPipelinePort, SessionRepositoryPort


@dataclass
class SubmitToPipelineUseCase:
    sessions: SessionRepositoryPort
    pipeline: AIPipelinePort

    async def execute(self, session_id: str) -> Session:
        session = await self._require(session_id)
        if session.assembled_prompt is None:
            raise ValueError("prompt must be built before pipeline submission")
        remote_id = await self.pipeline.submit(
            source_zip_path=Path(session.assembled_prompt.source_zip_path),
            instructions=session.assembled_prompt.instructions,
        )
        session.pipeline_remote_job_id = remote_id
        session.transition(SessionStatus.PIPELINE_SUBMITTED)
        await self.sessions.save(session)
        return session

    async def _require(self, session_id: str) -> Session:
        session = await self.sessions.get(session_id)
        if session is None:
            raise LookupError(f"session {session_id} not found")
        return session


@dataclass
class PollPipelineUseCase:
    sessions: SessionRepositoryPort
    pipeline: AIPipelinePort

    async def execute(self, session_id: str) -> PipelineJob:
        session = await self.sessions.get(session_id)
        if session is None:
            raise LookupError(f"session {session_id} not found")
        if not session.pipeline_remote_job_id:
            raise ValueError("session has no pipeline submission to poll")
        job = await self.pipeline.poll(remote_job_id=session.pipeline_remote_job_id)

        # Mirror upstream terminal state into our own FSM.
        if job.status == PipelineJobStatus.COMPLETED and session.status != SessionStatus.PIPELINE_COMPLETED:
            session.transition(SessionStatus.PIPELINE_COMPLETED)
            await self.sessions.save(session)
        elif job.status == PipelineJobStatus.FAILED and session.status != SessionStatus.PIPELINE_FAILED:
            session.transition(SessionStatus.PIPELINE_FAILED)
            await self.sessions.save(session)

        return job


@dataclass
class FetchPipelineResultUseCase:
    sessions: SessionRepositoryPort
    pipeline: AIPipelinePort

    async def execute(self, session_id: str) -> Path:
        session = await self.sessions.get(session_id)
        if session is None:
            raise LookupError(f"session {session_id} not found")
        if not session.pipeline_remote_job_id:
            raise ValueError("session has no pipeline submission")
        dest = settings.session_dir(session_id) / "pipeline-result" / "output.sh"
        path = await self.pipeline.fetch_result(
            remote_job_id=session.pipeline_remote_job_id, dest_path=dest
        )
        session.pipeline_result_path = str(path)
        await self.sessions.save(session)
        return path
