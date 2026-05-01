"""Use case: extract source code into the workspace and advance session FSM."""

from __future__ import annotations

from dataclasses import dataclass
from typing import BinaryIO

from ..domain import ExtractionKind, Session, SessionStatus
from ..ports import SessionRepositoryPort, SourceExtractorPort


@dataclass
class ExtractSourceUseCase:
    sessions: SessionRepositoryPort
    extractors: dict[ExtractionKind, SourceExtractorPort]

    async def execute_zip(self, *, session_id: str, file: BinaryIO) -> Session:
        session = await self._require(session_id)
        extractor = self._extractor(ExtractionKind.ZIP)
        result = await extractor.extract_zip(session_id=session_id, file=file)
        session.extraction_kind = result.extraction_kind
        session.source_uri = result.source_uri
        session.extracted_file_count = result.file_count
        session.transition(SessionStatus.EXTRACTED)
        await self.sessions.save(session)
        return session

    async def execute_github(
        self, *, session_id: str, kind: ExtractionKind, url: str, ref: str | None, pat: str | None
    ) -> Session:
        if kind not in (ExtractionKind.GITHUB_PUBLIC, ExtractionKind.GITHUB_PRIVATE):
            raise ValueError(f"unsupported extraction kind for github: {kind!r}")
        session = await self._require(session_id)
        extractor = self._extractor(kind)
        result = await extractor.extract_github(session_id=session_id, url=url, ref=ref, pat=pat)
        session.extraction_kind = kind
        session.source_uri = url
        session.extracted_file_count = result.file_count
        session.transition(SessionStatus.EXTRACTED)
        await self.sessions.save(session)
        return session

    async def _require(self, session_id: str) -> Session:
        session = await self.sessions.get(session_id)
        if session is None:
            raise LookupError(f"session {session_id} not found")
        return session

    def _extractor(self, kind: ExtractionKind) -> SourceExtractorPort:
        adapter = self.extractors.get(kind)
        if adapter is None:
            raise NotImplementedError(f"no extractor registered for {kind.value!r}")
        return adapter
