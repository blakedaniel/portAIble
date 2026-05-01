"""Assembled prompt value object."""

from __future__ import annotations

from pydantic import BaseModel


class AssembledPrompt(BaseModel):
    instructions: str
    source_zip_path: str
