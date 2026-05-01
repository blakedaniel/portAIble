"""Source extraction endpoints — ZIP upload (sync) + GitHub clone (async background)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from ..domain import ExtractionKind
from ..infrastructure.db import session_scope
from ..infrastructure.repos.sqlite_session_repo import SqliteSessionRepository
from ..ports import JobKind
from ..usecases import ExtractSourceUseCase
from .deps import get_extractors, get_job_registry, get_session_repo
from .schemas import GithubExtractRequest, JobIdResponse, Session

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


@router.post("/github", response_model=JobIdResponse, status_code=202)
async def extract_github(
    session_id: str,
    body: GithubExtractRequest,
    repo=Depends(get_session_repo),
    extractors=Depends(get_extractors),
    registry=Depends(get_job_registry),
):
    """Kick off a shallow `git clone` in the background. PAT is held in the
    closure and discarded when the job finishes; never persisted on the session.
    """
    session = await repo.get(session_id)
    if session is None:
        raise HTTPException(404, f"session {session_id} not found")

    if body.kind not in ("public", "private"):
        raise HTTPException(400, f"kind must be 'public' or 'private', got {body.kind!r}")
    kind = ExtractionKind.GITHUB_PUBLIC if body.kind == "public" else ExtractionKind.GITHUB_PRIVATE
    if kind is ExtractionKind.GITHUB_PRIVATE and not body.pat:
        raise HTTPException(400, "private extraction requires a personal access token")

    url = body.url
    ref = body.ref
    pat = body.pat  # captured in closure; not persisted

    async def job_body(on_progress):
        await on_progress(10, f"validating GitHub URL ({kind.value})")
        async with session_scope() as db:
            inner_repo = SqliteSessionRepository(db)
            await on_progress(30, "running git clone --depth 1")
            await ExtractSourceUseCase(sessions=inner_repo, extractors=extractors).execute_github(
                session_id=session_id, kind=kind, url=url, ref=ref, pat=pat,
            )
        await on_progress(95, "clone complete")

    job = await registry.submit(session_id=session_id, kind=JobKind.EXTRACT_GITHUB, body=job_body)
    return JobIdResponse(job_id=job.id)
