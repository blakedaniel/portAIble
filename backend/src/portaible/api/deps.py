"""FastAPI dependency wiring — adapter construction per request."""

from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..domain import ExtractionKind
from ..infrastructure.db import session_scope
from ..infrastructure.extractors.zip_extractor import ZipExtractor
from ..infrastructure.llm.fake_analyzer import FakeSourceAnalyzer
from ..infrastructure.pipeline.http_pipeline import HttpAIPipeline
from ..infrastructure.prompt_bank.filesystem_bank import FilesystemPromptBank
from ..infrastructure.repos.sqlite_job_repo import SqliteJobRepository
from ..infrastructure.repos.sqlite_session_repo import SqliteSessionRepository
from ..ports import (
    AIPipelinePort,
    JobRepositoryPort,
    PromptBankPort,
    SessionRepositoryPort,
    SourceAnalyzerPort,
    SourceExtractorPort,
)


async def get_db_session() -> AsyncIterator[AsyncSession]:
    async with session_scope() as db:
        yield db


def get_session_repo(db: AsyncSession = Depends(get_db_session)) -> SessionRepositoryPort:
    return SqliteSessionRepository(db)


def get_job_repo(db: AsyncSession = Depends(get_db_session)) -> JobRepositoryPort:
    return SqliteJobRepository(db)


def get_extractors() -> dict[ExtractionKind, SourceExtractorPort]:
    # Phase 1: only ZIP. GitHub adapters added in Phase 5.
    return {ExtractionKind.ZIP: ZipExtractor(workspace_root=Path(settings.workspace_dir))}


def get_source_analyzer() -> SourceAnalyzerPort:
    # Phase 1: fake analyzer. Replaced by DSPySourceAnalyzer in Phase 2.
    return FakeSourceAnalyzer()


def get_prompt_bank() -> PromptBankPort:
    return FilesystemPromptBank(root=settings.prompt_bank_dir)


def get_ai_pipeline() -> AIPipelinePort:
    return HttpAIPipeline()
