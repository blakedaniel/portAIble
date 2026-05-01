"""Design-decisions endpoints — generate (background), read, submit answers."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..domain import DecisionAnswer, DesignDecision
from ..infrastructure.db import session_scope
from ..infrastructure.repos.sqlite_session_repo import SqliteSessionRepository
from ..ports import JobKind
from ..usecases import GenerateDesignDecisionsUseCase, SubmitDesignAnswersUseCase
from .deps import get_design_decisions, get_job_registry, get_session_repo
from .schemas import JobIdResponse, Session

router = APIRouter(prefix="/api/sessions/{session_id}/decisions", tags=["decisions"])


class SubmitAnswersRequest(BaseModel):
    answers: list[DecisionAnswer]


@router.post("/generate", response_model=JobIdResponse, status_code=202)
async def generate_decisions(
    session_id: str,
    repo=Depends(get_session_repo),
    decisions_port=Depends(get_design_decisions),
    registry=Depends(get_job_registry),
):
    """Kick off DSPy decision generation in the background. Poll /jobs/{job_id}."""
    session = await repo.get(session_id)
    if session is None:
        raise HTTPException(404, f"session {session_id} not found")
    if session.source_profile is None or session.destination_profile is None:
        raise HTTPException(
            409, "both source and destination profiles must be confirmed first",
        )

    async def body(on_progress):
        await on_progress(10, "preparing decision context")
        async with session_scope() as db:
            inner_repo = SqliteSessionRepository(db)
            await on_progress(30, "running DSPy decision generator (LLM call)")
            await GenerateDesignDecisionsUseCase(
                sessions=inner_repo, decisions=decisions_port,
            ).execute(session_id)
        await on_progress(95, "persisted design decisions")

    job = await registry.submit(session_id=session_id, kind=JobKind.GENERATE_DECISIONS, body=body)
    return JobIdResponse(job_id=job.id)


@router.get("", response_model=list[DesignDecision])
async def get_decisions(session_id: str, repo=Depends(get_session_repo)):
    session = await repo.get(session_id)
    if session is None:
        raise HTTPException(404, "session not found")
    return session.design_decisions


@router.put("/answers", response_model=Session)
async def submit_answers(
    session_id: str,
    body: SubmitAnswersRequest,
    repo=Depends(get_session_repo),
):
    try:
        return await SubmitDesignAnswersUseCase(sessions=repo).execute(session_id, body.answers)
    except LookupError as e:
        raise HTTPException(404, str(e)) from e
    except ValueError as e:
        raise HTTPException(409, str(e)) from e
