"""Profile endpoints — analyze, read, update, confirm for source + destination."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ..usecases import (
    AnalyzeSourceUseCase,
    ConfirmDestinationProfileUseCase,
    ConfirmSourceProfileUseCase,
    SuggestDestinationUseCase,
    UpdateDestinationProfileUseCase,
    UpdateSourceProfileUseCase,
)
from .deps import get_session_repo, get_source_analyzer
from .schemas import DestinationProfile, Session, SourceProfile, SuggestDestinationRequest

router = APIRouter(prefix="/api/sessions/{session_id}", tags=["profiles"])


@router.post("/analyze", response_model=Session)
async def analyze(
    session_id: str,
    repo=Depends(get_session_repo),
    analyzer=Depends(get_source_analyzer),
):
    """Phase 1: synchronous analyzer (FakeSourceAnalyzer). Phase 2 makes this a background job."""
    try:
        return await AnalyzeSourceUseCase(sessions=repo, analyzer=analyzer).execute(session_id)
    except LookupError as e:
        raise HTTPException(404, str(e)) from e
    except ValueError as e:
        raise HTTPException(409, str(e)) from e


@router.get("/profiles/source", response_model=SourceProfile)
async def get_source_profile(session_id: str, repo=Depends(get_session_repo)):
    session = await repo.get(session_id)
    if session is None or session.source_profile is None:
        raise HTTPException(404, "no source profile yet")
    return session.source_profile


@router.put("/profiles/source", response_model=Session)
async def put_source_profile(
    session_id: str, profile: SourceProfile, repo=Depends(get_session_repo)
):
    try:
        return await UpdateSourceProfileUseCase(sessions=repo).execute(session_id, profile)
    except LookupError as e:
        raise HTTPException(404, str(e)) from e


@router.post("/profiles/source/confirm", response_model=Session)
async def confirm_source_profile(session_id: str, repo=Depends(get_session_repo)):
    try:
        return await ConfirmSourceProfileUseCase(sessions=repo).execute(session_id)
    except LookupError as e:
        raise HTTPException(404, str(e)) from e
    except ValueError as e:
        raise HTTPException(409, str(e)) from e


@router.post("/profiles/destination/suggest", response_model=Session)
async def suggest_destination_profile(
    session_id: str,
    body: SuggestDestinationRequest,
    repo=Depends(get_session_repo),
    analyzer=Depends(get_source_analyzer),
):
    try:
        return await SuggestDestinationUseCase(sessions=repo, analyzer=analyzer).execute(
            session_id, target_hint=body.target_hint
        )
    except LookupError as e:
        raise HTTPException(404, str(e)) from e
    except ValueError as e:
        raise HTTPException(409, str(e)) from e


@router.get("/profiles/destination", response_model=DestinationProfile)
async def get_destination_profile(session_id: str, repo=Depends(get_session_repo)):
    session = await repo.get(session_id)
    if session is None or session.destination_profile is None:
        raise HTTPException(404, "no destination profile yet")
    return session.destination_profile


@router.put("/profiles/destination", response_model=Session)
async def put_destination_profile(
    session_id: str, profile: DestinationProfile, repo=Depends(get_session_repo)
):
    try:
        return await UpdateDestinationProfileUseCase(sessions=repo).execute(session_id, profile)
    except LookupError as e:
        raise HTTPException(404, str(e)) from e


@router.post("/profiles/destination/confirm", response_model=Session)
async def confirm_destination_profile(session_id: str, repo=Depends(get_session_repo)):
    try:
        return await ConfirmDestinationProfileUseCase(sessions=repo).execute(session_id)
    except LookupError as e:
        raise HTTPException(404, str(e)) from e
    except ValueError as e:
        raise HTTPException(409, str(e)) from e
