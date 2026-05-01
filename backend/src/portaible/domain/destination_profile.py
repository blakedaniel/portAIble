"""Destination code profile — what we want the user to port the source code to."""

from __future__ import annotations

from pydantic import BaseModel, Field

from .source_profile import FrameworkEntry, LanguageEntry, PackageEntry


class DestinationProfile(BaseModel):
    languages: list[LanguageEntry] = Field(default_factory=list)
    frameworks: list[FrameworkEntry] = Field(default_factory=list)
    packages: list[PackageEntry] = Field(default_factory=list)
    target_notes: str = ""
    analyzer_draft: bool = True
