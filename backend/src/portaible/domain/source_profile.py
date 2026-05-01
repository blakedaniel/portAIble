"""Source code profile — what we extract from the source code via the analyzer."""

from __future__ import annotations

from pydantic import BaseModel, Field


class LanguageEntry(BaseModel):
    name: str
    version: str | None = None


class FrameworkEntry(BaseModel):
    name: str
    version: str | None = None


class PackageEntry(BaseModel):
    name: str
    version: str | None = None
    alternatives: list[str] = Field(default_factory=list)


class SourceProfile(BaseModel):
    languages: list[LanguageEntry] = Field(default_factory=list)
    frameworks: list[FrameworkEntry] = Field(default_factory=list)
    packages: list[PackageEntry] = Field(default_factory=list)
    important_information: str = ""
    analyzer_draft: bool = True
