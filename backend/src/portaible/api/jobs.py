"""Jobs endpoint — unified status poll for analyze / suggest / decisions / extract jobs."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from .deps import get_job_repo
from .schemas import JobDTO

router = APIRouter(prefix="/api/sessions/{session_id}/jobs", tags=["jobs"])


@router.get("/{job_id}", response_model=JobDTO)
async def get_job(session_id: str, job_id: str, repo=Depends(get_job_repo)):
    job = await repo.get(job_id)
    if job is None or job.session_id != session_id:
        raise HTTPException(404, "job not found")
    return JobDTO.from_domain(job)


@router.get("", response_model=list[JobDTO])
async def list_jobs(session_id: str, repo=Depends(get_job_repo)):
    jobs = await repo.list_for_session(session_id)
    return [JobDTO.from_domain(j) for j in jobs]
