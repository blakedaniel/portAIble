"""AI Pipeline proxy endpoints — submit, poll, fetch."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from ..usecases import (
    FetchPipelineResultUseCase,
    PollPipelineUseCase,
    SubmitToPipelineUseCase,
)
from .deps import get_ai_pipeline, get_session_repo
from .schemas import PipelineJob, Session

router = APIRouter(prefix="/api/sessions/{session_id}/pipeline", tags=["pipeline"])


@router.post("/submit", response_model=Session)
async def submit(
    session_id: str,
    repo=Depends(get_session_repo),
    pipeline=Depends(get_ai_pipeline),
):
    try:
        return await SubmitToPipelineUseCase(sessions=repo, pipeline=pipeline).execute(session_id)
    except LookupError as e:
        raise HTTPException(404, str(e)) from e
    except ValueError as e:
        raise HTTPException(409, str(e)) from e
    except Exception as e:
        raise HTTPException(502, f"pipeline submit failed: {e}") from e


@router.get("/status", response_model=PipelineJob)
async def status(
    session_id: str,
    repo=Depends(get_session_repo),
    pipeline=Depends(get_ai_pipeline),
):
    try:
        return await PollPipelineUseCase(sessions=repo, pipeline=pipeline).execute(session_id)
    except LookupError as e:
        raise HTTPException(404, str(e)) from e
    except ValueError as e:
        raise HTTPException(409, str(e)) from e
    except Exception as e:
        raise HTTPException(502, f"pipeline poll failed: {e}") from e


@router.get("/result")
async def fetch_result(
    session_id: str,
    repo=Depends(get_session_repo),
    pipeline=Depends(get_ai_pipeline),
):
    try:
        path = await FetchPipelineResultUseCase(sessions=repo, pipeline=pipeline).execute(session_id)
    except LookupError as e:
        raise HTTPException(404, str(e)) from e
    except ValueError as e:
        raise HTTPException(409, str(e)) from e
    except Exception as e:
        raise HTTPException(502, f"pipeline result fetch failed: {e}") from e
    return FileResponse(
        path, filename="output.sh", media_type="application/x-shellscript"
    )
