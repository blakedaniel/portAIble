"""Test fixtures — temp workspace + isolated DB per test."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

# Set env BEFORE importing portaible.config so AppSettings picks them up.
_TMP = tempfile.mkdtemp(prefix="portaible-test-")
os.environ["WORKSPACE_DIR"] = _TMP
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{Path(_TMP) / 'test.db'}"
os.environ["AI_PIPELINE_URL"] = "http://test-ai-pipeline.local"
os.environ["PROMPT_BANK_DIR"] = str(Path(__file__).resolve().parents[2] / "prompt-bank")


@pytest.fixture(scope="session", autouse=True)
def _workspace_root() -> Path:
    return Path(_TMP)
