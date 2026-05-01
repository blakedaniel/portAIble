"""Prompt assembly endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ..usecases import BuildPromptUseCase, UpdatePromptInstructionsUseCase
from .deps import get_prompt_bank, get_session_repo
from .schemas import AssembledPrompt, Session, UpdatePromptRequest

router = APIRouter(prefix="/api/sessions/{session_id}/prompt", tags=["prompt"])


@router.post("/build", response_model=Session)
async def build_prompt(
    session_id: str,
    repo=Depends(get_session_repo),
    bank=Depends(get_prompt_bank),
    skip_decisions: bool = True,
):
    try:
        return await BuildPromptUseCase(sessions=repo, bank=bank).execute(
            session_id, allow_skip_decisions=skip_decisions
        )
    except LookupError as e:
        raise HTTPException(404, str(e)) from e
    except (ValueError, FileNotFoundError) as e:
        raise HTTPException(409, str(e)) from e


@router.get("", response_model=AssembledPrompt)
async def get_prompt(session_id: str, repo=Depends(get_session_repo)):
    session = await repo.get(session_id)
    if session is None or session.assembled_prompt is None:
        raise HTTPException(404, "no assembled prompt yet")
    return session.assembled_prompt


@router.put("", response_model=Session)
async def update_prompt(
    session_id: str,
    body: UpdatePromptRequest,
    repo=Depends(get_session_repo),
):
    try:
        return await UpdatePromptInstructionsUseCase(sessions=repo).execute(
            session_id, body.instructions
        )
    except LookupError as e:
        raise HTTPException(404, str(e)) from e
    except ValueError as e:
        raise HTTPException(409, str(e)) from e
