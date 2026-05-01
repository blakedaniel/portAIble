"""DSPy-backed SourceAnalyzer — replaces FakeSourceAnalyzer in Phase 2."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

import dspy

from ...config import settings
from ...domain import DestinationProfile, SourceProfile
from ...ports import SourceAnalyzerPort
from .dspy_config import create_dspy_lm
from .signatures import (
    DestinationProfileSuggestionSignature,
    FileSnippet,
    SourceProfileSignature,
)
from .source_picker import list_files, pick_representative

logger = logging.getLogger(__name__)


class DSPySourceAnalyzer(SourceAnalyzerPort):
    def __init__(self, model: str | None = None, suggest_model: str | None = None):
        self.model = model or settings.source_analyzer_model
        self.suggest_model = suggest_model or settings.destination_suggest_model

    async def analyze(self, *, source_dir: Path) -> SourceProfile:
        if not source_dir.is_dir():
            raise FileNotFoundError(f"source dir does not exist: {source_dir}")

        listing = list_files(source_dir)
        snippets = pick_representative(
            source_dir,
            max_files=settings.analyzer_max_files,
            max_file_bytes=settings.analyzer_max_file_bytes,
        )
        rep_files = [FileSnippet(path=p, content=c) for p, c in snippets]

        logger.info(
            "[analyzer] dir=%s files=%d representative=%d model=%s",
            source_dir, len(listing), len(rep_files), self.model,
        )

        lm = create_dspy_lm(settings, model_override=self.model)
        module = dspy.Predict(SourceProfileSignature)

        def _run():
            with dspy.context(lm=lm):
                return module(
                    file_listing="\n".join(listing[:1000]),
                    representative_files=rep_files,
                )

        pred = await asyncio.to_thread(_run)
        return SourceProfile(
            languages=list(getattr(pred, "languages", []) or []),
            frameworks=list(getattr(pred, "frameworks", []) or []),
            packages=list(getattr(pred, "packages", []) or []),
            important_information=getattr(pred, "important_information", "") or "",
            analyzer_draft=True,
        )

    async def suggest_destination(
        self, *, source_profile: SourceProfile, target_hint: str | None
    ) -> DestinationProfile:
        lm = create_dspy_lm(settings, model_override=self.suggest_model)
        module = dspy.Predict(DestinationProfileSuggestionSignature)

        def _run():
            with dspy.context(lm=lm):
                return module(
                    source_profile_json=source_profile.model_dump_json(),
                    target_hint=target_hint or "",
                )

        pred = await asyncio.to_thread(_run)
        return DestinationProfile(
            languages=list(getattr(pred, "languages", []) or []),
            frameworks=list(getattr(pred, "frameworks", []) or []),
            packages=list(getattr(pred, "packages", []) or []),
            target_notes=getattr(pred, "target_notes", "") or "",
            analyzer_draft=True,
        )
