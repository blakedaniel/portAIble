"""Profile endpoints — analyze (background job), read, update, confirm for source + destination."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ..infrastructure.db import session_scope
from ..infrastructure.repos.sqlite_session_repo import SqliteSessionRepository
from ..ports import JobKind
from ..usecases import (
    AnalyzeSourceUseCase,
    ConfirmDestinationProfileUseCase,
    ConfirmSourceProfileUseCase,
    SuggestDestinationUseCase,
    UpdateDestinationProfileUseCase,
    UpdateSourceProfileUseCase,
)
from .deps import get_job_registry, get_session_repo, get_source_analyzer
from .schemas import DestinationProfile, JobIdResponse, Session, SourceProfile, SuggestDestinationRequest

router = APIRouter(prefix="/api/sessions/{session_id}", tags=["profiles"])


@router.post("/analyze", response_model=JobIdResponse, status_code=202)
async def analyze(
    session_id: str,
    repo=Depends(get_session_repo),
    analyzer=Depends(get_source_analyzer),
    registry=Depends(get_job_registry),
):
    """Kick off the SourceAnalyzer in the background. Poll /jobs/{job_id} for status."""
    session = await repo.get(session_id)
    if session is None:
        raise HTTPException(404, f"session {session_id} not found")

    async def body(on_progress):
        await on_progress(5, "preparing analyzer inputs")
        # Open a fresh DB session inside the background task — the request scope is gone.
        async with session_scope() as db:
            inner_repo = SqliteSessionRepository(db)
            await on_progress(20, "running DSPy analyzer (LLM call)")
            await AnalyzeSourceUseCase(sessions=inner_repo, analyzer=analyzer).execute(session_id)
        await on_progress(95, "persisted source profile")

    job = await registry.submit(session_id=session_id, kind=JobKind.ANALYZE, body=body)
    return JobIdResponse(job_id=job.id)


@router.post("/analyze/sync", response_model=Session, include_in_schema=False)
async def analyze_sync(
    session_id: str,
    repo=Depends(get_session_repo),
    analyzer=Depends(get_source_analyzer),
):
    """Synchronous analyze for tests / debugging — same use case, no background task."""
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
