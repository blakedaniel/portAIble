"""FastAPI dependency wiring — adapter construction per request."""

from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..domain import ExtractionKind
from ..infrastructure.db import session_scope
from ..infrastructure.extractors.github_extractor import GithubSourceExtractor
from ..infrastructure.extractors.zip_extractor import ZipExtractor
from ..infrastructure.llm.dspy_analyzer import DSPySourceAnalyzer
from ..infrastructure.llm.dspy_decisions import DSPyDesignDecisions
from ..infrastructure.llm.fake_analyzer import FakeSourceAnalyzer
from ..infrastructure.llm.fake_decisions import FakeDesignDecisions
from ..infrastructure.pipeline.http_pipeline import HttpAIPipeline
from ..infrastructure.prompt_bank.filesystem_bank import FilesystemPromptBank
from ..infrastructure.repos.sqlite_job_repo import SqliteJobRepository
from ..infrastructure.repos.sqlite_session_repo import SqliteSessionRepository
from ..jobs import JobRegistry
from ..ports import (
    AIPipelinePort,
    DesignDecisionsPort,
    JobRepositoryPort,
    PromptBankPort,
    SessionRepositoryPort,
    SourceAnalyzerPort,
    SourceExtractorPort,
)

# Set USE_FAKE_ANALYZER=true in tests / local dev without Ollama.
import os as _os
_USE_FAKE_ANALYZER = _os.getenv("USE_FAKE_ANALYZER", "").lower() in ("1", "true", "yes")

# Process-wide JobRegistry (in-process; jobs persist via SQLite).
_job_registry = JobRegistry()


async def get_db_session() -> AsyncIterator[AsyncSession]:
    async with session_scope() as db:
        yield db


def get_session_repo(db: AsyncSession = Depends(get_db_session)) -> SessionRepositoryPort:
    return SqliteSessionRepository(db)


def get_job_repo(db: AsyncSession = Depends(get_db_session)) -> JobRepositoryPort:
    return SqliteJobRepository(db)


def get_extractors() -> dict[ExtractionKind, SourceExtractorPort]:
    workspace = Path(settings.workspace_dir)
    return {
        ExtractionKind.ZIP: ZipExtractor(workspace_root=workspace),
        ExtractionKind.GITHUB_PUBLIC: GithubSourceExtractor(
            kind=ExtractionKind.GITHUB_PUBLIC, workspace_root=workspace,
        ),
        ExtractionKind.GITHUB_PRIVATE: GithubSourceExtractor(
            kind=ExtractionKind.GITHUB_PRIVATE, workspace_root=workspace,
        ),
    }


def get_source_analyzer() -> SourceAnalyzerPort:
    """Real DSPy analyzer in production; FakeSourceAnalyzer when USE_FAKE_ANALYZER=true."""
    return FakeSourceAnalyzer() if _USE_FAKE_ANALYZER else DSPySourceAnalyzer()


def get_design_decisions() -> DesignDecisionsPort:
    """Real DSPy decision generator in production; Fake when USE_FAKE_ANALYZER=true."""
    return FakeDesignDecisions() if _USE_FAKE_ANALYZER else DSPyDesignDecisions()


def get_job_registry() -> JobRegistry:
    return _job_registry


def get_prompt_bank() -> PromptBankPort:
    return FilesystemPromptBank(root=settings.prompt_bank_dir)


def get_ai_pipeline() -> AIPipelinePort:
    return HttpAIPipeline()
