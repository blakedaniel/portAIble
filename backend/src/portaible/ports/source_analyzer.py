"""SourceAnalyzerPort — DSPy-backed analysis of extracted source code."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from ..domain import DestinationProfile, SourceProfile


class SourceAnalyzerPort(ABC):
    @abstractmethod
    async def analyze(self, *, source_dir: Path) -> SourceProfile:
        ...

    @abstractmethod
    async def suggest_destination(
        self,
        *,
        source_profile: SourceProfile,
        target_hint: str | None,
    ) -> DestinationProfile:
        ...
