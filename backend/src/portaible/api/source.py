"""Source extraction endpoints — ZIP upload (sync) + GitHub stub for Phase 5."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from ..usecases import ExtractSourceUseCase
from .deps import get_extractors, get_session_repo
from .schemas import GithubExtractRequest, Session

router = APIRouter(prefix="/api/sessions/{session_id}/source", tags=["source"])


@router.post("/zip", response_model=Session)
async def extract_zip(
    session_id: str,
    file: UploadFile = File(...),
    repo=Depends(get_session_repo),
    extractors=Depends(get_extractors),
):
    use_case = ExtractSourceUseCase(sessions=repo, extractors=extractors)
    try:
        return await use_case.execute_zip(session_id=session_id, file=file.file)
    except LookupError as e:
        raise HTTPException(404, str(e)) from e
    except Exception as e:
        raise HTTPException(500, f"extraction failed: {e}") from e


@router.post("/github", response_model=Session, status_code=501)
async def extract_github(session_id: str, body: GithubExtractRequest):
    raise HTTPException(501, "GitHub extraction lands in Phase 5")
