"""AIPipelinePort — proxies submission/poll/result to local-chat-agent."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from ..domain import PipelineJob


class AIPipelinePort(ABC):
    @abstractmethod
    async def submit(self, *, source_zip_path: Path, instructions: str) -> str:
        """Submit and return the remote job_id."""
        ...

    @abstractmethod
    async def poll(self, *, remote_job_id: str) -> PipelineJob:
        ...

    @abstractmethod
    async def fetch_result(self, *, remote_job_id: str, dest_path: Path) -> Path:
        """Stream result to dest_path and return its path."""
        ...
