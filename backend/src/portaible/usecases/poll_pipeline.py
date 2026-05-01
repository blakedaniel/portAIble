"""PollPipelineUseCase — proxies status from local-chat-agent and advances FSM on terminal states."""

from __future__ import annotations

from dataclasses import dataclass

from ..domain import PipelineJob, PipelineJobStatus, SessionStatus
from ..ports import AIPipelinePort, SessionRepositoryPort


@dataclass
class PollPipelineUseCase:
    sessions: SessionRepositoryPort
    pipeline: AIPipelinePort

    async def execute(self, *, session_id: str) -> PipelineJob:
        session = await self.sessions.get(session_id)
        if session is None:
            raise LookupError(f"session not found: {session_id}")
        if session.pipeline_job is None:
            raise ValueError("session has not submitted to the pipeline yet")

        upstream = await self.pipeline.poll(remote_job_id=session.pipeline_job.remote_job_id)
        upstream.result_path = session.pipeline_job.result_path

        if upstream.status == PipelineJobStatus.COMPLETED \
                and session.status != SessionStatus.PIPELINE_COMPLETED:
            session.pipeline_job = upstream
            session.advance_to(SessionStatus.PIPELINE_COMPLETED)
            await self.sessions.save(session)
        elif upstream.status == PipelineJobStatus.FAILED \
                and session.status != SessionStatus.PIPELINE_FAILED:
            session.pipeline_job = upstream
            session.advance_to(SessionStatus.PIPELINE_FAILED)
            await self.sessions.save(session)

        return upstream
