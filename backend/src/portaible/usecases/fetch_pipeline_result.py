"""FetchPipelineResultUseCase — downloads the upstream result and saves it under the session dir."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..config import settings
from ..ports import AIPipelinePort, SessionRepositoryPort


@dataclass
class FetchPipelineResultUseCase:
    sessions: SessionRepositoryPort
    pipeline: AIPipelinePort

    async def execute(self, *, session_id: str) -> Path:
        session = await self.sessions.get(session_id)
        if session is None:
            raise LookupError(f"session not found: {session_id}")
        if session.pipeline_job is None:
            raise ValueError("session has no pipeline job to fetch")

        # local-chat-agent currently returns a single shell script (output.sh)
        dest = settings.session_dir(session_id) / "pipeline-result" / "output.sh"
        await self.pipeline.fetch_result(
            remote_job_id=session.pipeline_job.remote_job_id, dest_path=dest
        )
        session.pipeline_job.result_path = str(dest)
        await self.sessions.save(session)
        return dest
