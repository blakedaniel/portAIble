"""Phase 4: design decisions wizard — generate (background), read, submit answers."""

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


def _confirm_both_profiles(client: TestClient, _workspace_root: Path) -> str:
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
    return sid


def test_generate_decisions_runs_as_background_job(client: TestClient, _workspace_root: Path):
    sid = _confirm_both_profiles(client, _workspace_root)

    resp = client.post(f"/api/sessions/{sid}/decisions/generate")
    assert resp.status_code == 202, resp.text
    job_id = resp.json()["job_id"]

    final = _wait_for_job(client, sid, job_id)
    assert final["status"] == "completed", f"job ended {final['status']}: {final.get('error')}"

    decisions = client.get(f"/api/sessions/{sid}/decisions").json()
    assert isinstance(decisions, list) and len(decisions) >= 3
    # FakeDesignDecisions returns these three canned ids.
    ids = {d["id"] for d in decisions}
    assert {"persistence-layer", "auth-strategy", "build-tool"} <= ids


def test_generate_409_when_profiles_not_confirmed(client: TestClient):
    sid = client.post("/api/sessions").json()["id"]
    resp = client.post(f"/api/sessions/{sid}/decisions/generate")
    assert resp.status_code == 409


def test_submit_answers_advances_session(client: TestClient, _workspace_root: Path):
    sid = _confirm_both_profiles(client, _workspace_root)
    job_id = client.post(f"/api/sessions/{sid}/decisions/generate").json()["job_id"]
    _wait_for_job(client, sid, job_id)

    decisions = client.get(f"/api/sessions/{sid}/decisions").json()
    answers = [
        {"decision_id": d["id"],
         "selected_option_id": d["options"][0]["id"],
         "freeform_answer": None}
        for d in decisions
    ]

    resp = client.put(f"/api/sessions/{sid}/decisions/answers", json={"answers": answers})
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "decisions_answered"

    # And the assembled prompt now includes the answered decisions.
    client.post(f"/api/sessions/{sid}/prompt/build")
    prompt = client.get(f"/api/sessions/{sid}/prompt").json()
    assert "Persistence" in prompt["instructions"] or "persistence" in prompt["instructions"].lower()


def test_submit_unknown_decision_id_409(client: TestClient, _workspace_root: Path):
    sid = _confirm_both_profiles(client, _workspace_root)
    job_id = client.post(f"/api/sessions/{sid}/decisions/generate").json()["job_id"]
    _wait_for_job(client, sid, job_id)

    resp = client.put(
        f"/api/sessions/{sid}/decisions/answers",
        json={"answers": [{"decision_id": "nope", "selected_option_id": "x", "freeform_answer": None}]},
    )
    assert resp.status_code == 409
