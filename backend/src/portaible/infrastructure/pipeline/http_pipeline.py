"""HttpAIPipeline — calls local-chat-agent's /chat endpoint over HTTP.

Validated against /home/blake/programs/local-chat-agent/src/local_chat_agent/routes/chat.py:
- POST /chat (multipart: file=<zip>, instructions=<str>) -> {"job_id": "<12hex>"}
- GET /chat/jobs/{id} -> {job_id, status, progress_percentage, progress_message, error}
- GET /chat/jobs/{id}/result -> FileResponse(output.sh, application/x-shellscript)
"""

from __future__ import annotations

import logging
from pathlib import Path

import httpx

from ...config import settings
from ...domain import PipelineJob, PipelineJobStatus
from ...ports import AIPipelinePort

logger = logging.getLogger(__name__)


class HttpAIPipeline(AIPipelinePort):
    def __init__(self, base_url: str | None = None, timeout: float | None = None):
        self.base_url = (base_url or settings.ai_pipeline_url).rstrip("/")
        self.timeout = timeout if timeout is not None else float(settings.ai_pipeline_timeout)

    async def submit(self, *, source_zip_path: Path, instructions: str) -> str:
        with open(source_zip_path, "rb") as f:
            files = {"file": (source_zip_path.name, f, "application/zip")}
            data = {"instructions": instructions}
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(f"{self.base_url}/chat", files=files, data=data)
        resp.raise_for_status()
        body = resp.json()
        job_id = body.get("job_id")
        if not job_id:
            raise RuntimeError(f"AI pipeline submit returned no job_id: {body!r}")
        logger.info("[ai-pipeline] submit -> job_id=%s", job_id)
        return job_id

    async def poll(self, *, remote_job_id: str) -> PipelineJob:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(f"{self.base_url}/chat/jobs/{remote_job_id}")
        resp.raise_for_status()
        body = resp.json()
        return PipelineJob(
            remote_job_id=body.get("job_id", remote_job_id),
            status=PipelineJobStatus(body.get("status", "pending")),
            progress_percentage=int(body.get("progress_percentage", 0) or 0),
            progress_message=body.get("progress_message", "") or "",
            error=body.get("error"),
        )

    async def fetch_result(self, *, remote_job_id: str, dest_path: Path) -> Path:
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream("GET", f"{self.base_url}/chat/jobs/{remote_job_id}/result") as resp:
                resp.raise_for_status()
                with open(dest_path, "wb") as f:
                    async for chunk in resp.aiter_bytes():
                        f.write(chunk)
        logger.info("[ai-pipeline] result downloaded job=%s -> %s", remote_job_id, dest_path)
        return dest_path
