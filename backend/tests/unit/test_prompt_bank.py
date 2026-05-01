"""FilesystemPromptBank — slug normalization + lookup."""

from __future__ import annotations

from pathlib import Path

import pytest

from portaible.infrastructure.prompt_bank.filesystem_bank import FilesystemPromptBank, _slugify


@pytest.mark.parametrize("name,expected", [
    ("Spring Boot 3.5", "springboot"),
    ("Spring Boot", "springboot"),
    ("Nuxt 2", "nuxt2"),       # version-suffixed framework variants stay distinct
    ("Django", "django"),
    ("Python 3.11", "python"),
    ("C#", "csharp"),
    ("C++", "cpp"),
    (".NET", "dotnet"),
    ("FastAPI 0.110", "fastapi"),
])
def test_slugify(name, expected):
    assert _slugify(name) == expected


def test_lookup_hits_seeded_files(tmp_path: Path):
    # Use the real bundled prompt-bank to assert seed files are reachable.
    bank = FilesystemPromptBank(root=Path(__file__).resolve().parents[3] / "prompt-bank")
    assert bank.fetch_framework_doc("Django") is not None
    assert bank.fetch_framework_doc("Spring Boot 3.5") is not None
    assert bank.fetch_transition_doc("Django", "Spring Boot") is not None


def test_lookup_misses_returns_none(tmp_path: Path):
    bank = FilesystemPromptBank(root=tmp_path)  # empty
    assert bank.fetch_framework_doc("Django") is None
    assert bank.fetch_language_doc("Python") is None


def test_index_lists_existing_docs():
    bank = FilesystemPromptBank(root=Path(__file__).resolve().parents[3] / "prompt-bank")
    idx = bank.index()
    assert "django" in idx["frameworks"]
    assert "springboot" in idx["frameworks"]
    assert "django-springboot" in idx["transitions"]
