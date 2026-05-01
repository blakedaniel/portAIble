"""SourceExtractorPort — abstract source extraction (zip / GitHub) into the workspace."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO

from ..domain import ExtractionKind


@dataclass(frozen=True)
class ExtractionResult:
    workspace_src_dir: Path
    file_count: int
    top_level_listing: list[str]
    extraction_kind: ExtractionKind
    source_uri: str | None


class SourceExtractorPort(ABC):
    """A single extractor adapter handles one ExtractionKind."""

    kind: ExtractionKind

    @abstractmethod
    async def extract_zip(
        self, *, session_id: str, file: BinaryIO
    ) -> ExtractionResult:
        """Used only by the zip adapter; raises NotImplementedError otherwise."""
        raise NotImplementedError

    @abstractmethod
    async def extract_github(
        self,
        *,
        session_id: str,
        url: str,
        ref: str | None = None,
        pat: str | None = None,
    ) -> ExtractionResult:
        """Used only by the github adapter; raises NotImplementedError otherwise."""
        raise NotImplementedError
