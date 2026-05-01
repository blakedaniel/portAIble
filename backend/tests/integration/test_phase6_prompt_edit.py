"""Phase 6: editing the assembled prompt before submission."""

from __future__ import annotations

import io
import time
import zipfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def app():
    from portaible.app import app as fastapi_app
    return fastapi_app


@pytest.fixture
def client(app):
    with TestClient(app) as c:
        yield c


def _make_zip() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("manage.py", "import django\n")
        z.writestr("requirements.txt", "Django==4.2\n")
    return buf.getvalue()


def _wait_for_job(client: TestClient, sid: str, jid: str, timeout: float = 5.0) -> dict:
    deadline = time.time() + timeout
    while time.time() < deadline:
        body = client.get(f"/api/sessions/{sid}/jobs/{jid}").json()
        if body["status"] in ("completed", "failed"):
            return body
        time.sleep(0.05)
    pytest.fail(f"job {jid} never finished within {timeout}s")


def _build_prompt(client: TestClient) -> str:
    """Drive a session through the wizard to a freshly built prompt; return sid."""
    sid = client.post("/api/sessions").json()["id"]
    client.post(
        f"/api/sessions/{sid}/source/zip",
        files={"file": ("a.zip", _make_zip(), "application/zip")},
    )
    job = client.post(f"/api/sessions/{sid}/analyze").json()
    _wait_for_job(client, sid, job["job_id"])
    client.post(f"/api/sessions/{sid}/profiles/source/confirm")
    client.post(
        f"/api/sessions/{sid}/profiles/destination/suggest",
        json={"target_hint": "Spring Boot 3.5"},
    )
    client.post(f"/api/sessions/{sid}/profiles/destination/confirm")
    resp = client.post(f"/api/sessions/{sid}/prompt/build")
    assert resp.status_code == 200, resp.text
    return sid


def test_put_prompt_persists_edited_instructions(client: TestClient, _workspace_root: Path):
    sid = _build_prompt(client)

    edited = "# Edited!\n\nMy custom override of the assembled prompt."
    resp = client.put(f"/api/sessions/{sid}/prompt", json={"instructions": edited})
    assert resp.status_code == 200, resp.text
    assert resp.json()["assembled_prompt"]["instructions"] == edited

    # Reading back via GET /prompt confirms persistence (separate request scope).
    got = client.get(f"/api/sessions/{sid}/prompt").json()
    assert got["instructions"] == edited


def test_put_prompt_empty_body_rejected(client: TestClient, _workspace_root: Path):
    sid = _build_prompt(client)
    resp = client.put(f"/api/sessions/{sid}/prompt", json={"instructions": "   \n  "})
    assert resp.status_code == 409


def test_put_prompt_locked_after_pipeline_submit(client: TestClient, _workspace_root: Path):
    sid = _build_prompt(client)

    # Force-transition the session to PIPELINE_SUBMITTED via the repo so we don't need a live pipeline.
    import asyncio

    from portaible.domain import SessionStatus
    from portaible.infrastructure.db import session_scope
    from portaible.infrastructure.repos.sqlite_session_repo import SqliteSessionRepository

    async def _advance():
        async with session_scope() as db:
            repo = SqliteSessionRepository(db)
            session = await repo.get(sid)
            assert session is not None
            session.transition(SessionStatus.PIPELINE_SUBMITTED)
            await repo.save(session)

    asyncio.run(_advance())

    resp = client.put(f"/api/sessions/{sid}/prompt", json={"instructions": "anything"})
    assert resp.status_code == 409


def test_put_prompt_404_when_no_prompt_built(client: TestClient, _workspace_root: Path):
    sid = client.post("/api/sessions").json()["id"]
    resp = client.put(f"/api/sessions/{sid}/prompt", json={"instructions": "hello"})
    assert resp.status_code == 409
    assert "build it first" in resp.json()["detail"]
