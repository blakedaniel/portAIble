"""Prompt-bank inspection endpoint — used by the UI to hint available bank docs."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from .deps import get_prompt_bank

router = APIRouter(prefix="/api/prompt-bank", tags=["prompt-bank"])


@router.get("/index")
async def index(bank=Depends(get_prompt_bank)) -> dict:
    return bank.index()
