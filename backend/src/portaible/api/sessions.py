"""Session lifecycle endpoints: create, list, get, delete."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ..usecases import CreateSessionUseCase
from .deps import get_session_repo
from .schemas import Session, SessionListResponse

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.post("", response_model=Session, status_code=201)
async def create_session(repo=Depends(get_session_repo)):
    return await CreateSessionUseCase(sessions=repo).execute()


@router.get("", response_model=SessionListResponse)
async def list_sessions(repo=Depends(get_session_repo)):
    return SessionListResponse.from_summaries(await repo.list())


@router.get("/{session_id}", response_model=Session)
async def get_session(session_id: str, repo=Depends(get_session_repo)):
    session = await repo.get(session_id)
    if session is None:
        raise HTTPException(404, "session not found")
    return session


@router.delete("/{session_id}", status_code=204)
async def delete_session(session_id: str, repo=Depends(get_session_repo)):
    await repo.delete(session_id)
