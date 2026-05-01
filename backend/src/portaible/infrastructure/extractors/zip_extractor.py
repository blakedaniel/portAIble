"""ZIP-based source extractor — pattern mirrors local-chat-agent's ZipExtractor."""

from __future__ import annotations

import logging
import os
import shutil
import zipfile
from pathlib import Path
from typing import BinaryIO

from ...config import settings
from ...domain import ExtractionKind
from ...ports import ExtractionResult, SourceExtractorPort

logger = logging.getLogger(__name__)


class ZipExtractor(SourceExtractorPort):
    kind = ExtractionKind.ZIP

    def __init__(self, workspace_root: Path | None = None):
        self.workspace_root = workspace_root or Path(settings.workspace_dir)

    async def extract_zip(self, *, session_id: str, file: BinaryIO) -> ExtractionResult:
        session_dir = self.workspace_root / "sessions" / session_id
        src_dir = session_dir / "src"
        if src_dir.exists():
            shutil.rmtree(src_dir)
        src_dir.mkdir(parents=True, exist_ok=True)

        zip_path = session_dir / "upload.zip"
        with open(zip_path, "wb") as f:
            shutil.copyfileobj(file, f)

        with zipfile.ZipFile(zip_path, "r") as z:
            z.extractall(src_dir)

        # Drop the upload after extraction; source.zip is regenerated at submit time.
        try:
            os.remove(zip_path)
        except OSError:
            pass

        file_count = 0
        listing: list[str] = []
        for dirpath, _, filenames in os.walk(src_dir):
            for fname in filenames:
                if fname.startswith("._") or fname == ".DS_Store":
                    continue
                full = Path(dirpath) / fname
                rel = full.relative_to(src_dir)
                if file_count < 50:
                    listing.append(str(rel))
                file_count += 1

        logger.info("[zip-extract] session=%s files=%d dest=%s", session_id, file_count, src_dir)
        return ExtractionResult(
            workspace_src_dir=src_dir,
            file_count=file_count,
            top_level_listing=sorted(listing),
            extraction_kind=ExtractionKind.ZIP,
            source_uri=None,
        )

    async def extract_github(
        self, *, session_id: str, url: str, ref: str | None = None, pat: str | None = None
    ) -> ExtractionResult:
        raise NotImplementedError("ZipExtractor does not support GitHub extraction")
