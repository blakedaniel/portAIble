"""Phase 3: destination profile suggestion + manual edit + confirm.

This test exists to give Phase 3 a distinguishable verification artifact —
the use cases and API endpoints landed during Phase 1+2 linter scaffolding,
but no test directly exercised the destination flow until now.
"""

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


def _to_analyzed(client: TestClient) -> str:
    sid = client.post("/api/sessions").json()["id"]
    client.post(
        f"/api/sessions/{sid}/source/zip",
        files={"file": ("a.zip", _make_zip(), "application/zip")},
    )
    job = client.post(f"/api/sessions/{sid}/analyze").json()
    _wait_for_job(client, sid, job["job_id"])
    client.post(f"/api/sessions/{sid}/profiles/source/confirm")
    return sid


def test_suggest_destination_populates_profile(client: TestClient, _workspace_root: Path):
    sid = _to_analyzed(client)
    resp = client.post(
        f"/api/sessions/{sid}/profiles/destination/suggest",
        json={"target_hint": "Spring Boot 3.5"},
    )
    assert resp.status_code == 200, resp.text
    session = resp.json()
    assert session["destination_profile"] is not None
    profile = session["destination_profile"]
    assert profile["analyzer_draft"] is True
    # FakeSourceAnalyzer canned response
    assert profile["frameworks"][0]["name"] == "Spring Boot"


def test_user_edit_via_put_drops_draft_flag(client: TestClient, _workspace_root: Path):
    sid = _to_analyzed(client)
    suggested = client.post(
        f"/api/sessions/{sid}/profiles/destination/suggest",
        json={"target_hint": None},
    ).json()["destination_profile"]

    suggested["target_notes"] = "User-edited notes."
    suggested["analyzer_draft"] = False
    resp = client.put(f"/api/sessions/{sid}/profiles/destination", json=suggested)
    assert resp.status_code == 200
    saved = resp.json()["destination_profile"]
    assert saved["target_notes"] == "User-edited notes."
    assert saved["analyzer_draft"] is False


def test_confirm_advances_session_status(client: TestClient, _workspace_root: Path):
    sid = _to_analyzed(client)
    client.post(
        f"/api/sessions/{sid}/profiles/destination/suggest",
        json={"target_hint": "Spring Boot"},
    )
    resp = client.post(f"/api/sessions/{sid}/profiles/destination/confirm")
    assert resp.status_code == 200
    assert resp.json()["status"] == "destination_profile_confirmed"


def test_suggest_404_on_missing_session(client: TestClient):
    resp = client.post(
        "/api/sessions/deadbeef/profiles/destination/suggest", json={"target_hint": None},
    )
    assert resp.status_code == 404
