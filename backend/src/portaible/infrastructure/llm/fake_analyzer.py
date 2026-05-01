"""FakeSourceAnalyzer — Phase 1 stand-in returning a canned Django profile.

Replaced by DSPySourceAnalyzer in Phase 2. Lets the vertical slice run without Ollama.
"""

from __future__ import annotations

from pathlib import Path

from ...domain import (
    DestinationProfile,
    FrameworkEntry,
    LanguageEntry,
    PackageEntry,
    SourceProfile,
)
from ...ports import SourceAnalyzerPort


class FakeSourceAnalyzer(SourceAnalyzerPort):
    async def analyze(self, *, source_dir: Path) -> SourceProfile:
        return SourceProfile(
            languages=[LanguageEntry(name="Python", version="3.11")],
            frameworks=[FrameworkEntry(name="Django", version="4.2")],
            packages=[
                PackageEntry(
                    name="djangorestframework",
                    version="3.14",
                    alternatives=["django-ninja", "fastapi-equivalent endpoint"],
                ),
                PackageEntry(name="psycopg2", version="2.9", alternatives=["asyncpg"]),
            ],
            important_information=(
                "Canned Phase-1 profile (FakeSourceAnalyzer). Real DSPy-driven analysis lands in Phase 2."
            ),
            analyzer_draft=True,
        )

    async def suggest_destination(
        self, *, source_profile: SourceProfile, target_hint: str | None
    ) -> DestinationProfile:
        return DestinationProfile(
            languages=[LanguageEntry(name="Java", version="21")],
            frameworks=[FrameworkEntry(name="Spring Boot", version="3.5")],
            packages=[
                PackageEntry(name="spring-boot-starter-web"),
                PackageEntry(name="spring-boot-starter-data-jpa"),
            ],
            target_notes=f"Canned Phase-1 destination (target_hint={target_hint!r}).",
            analyzer_draft=True,
        )
