"""Phase 2: background analyze job — submit, poll until completed, verify profile lands."""

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


def test_analyze_runs_as_background_job(client: TestClient, _workspace_root: Path):
    sid = client.post("/api/sessions").json()["id"]
    client.post(
        f"/api/sessions/{sid}/source/zip",
        files={"file": ("a.zip", _make_zip(), "application/zip")},
    )

    # Kick off the analyze job.
    resp = client.post(f"/api/sessions/{sid}/analyze")
    assert resp.status_code == 202, resp.text
    job_id = resp.json()["job_id"]
    assert len(job_id) == 12

    # Poll until completed (FakeSourceAnalyzer is fast — should resolve in well under a second).
    deadline = time.time() + 5.0
    final = None
    while time.time() < deadline:
        r = client.get(f"/api/sessions/{sid}/jobs/{job_id}")
        assert r.status_code == 200, r.text
        body = r.json()
        if body["status"] in ("completed", "failed"):
            final = body
            break
        time.sleep(0.05)

    assert final is not None, "background job never finished"
    assert final["status"] == "completed", f"job ended {final['status']}: {final.get('error')}"
    assert final["progress_percentage"] == 100

    # The session should have the analyzer-drafted profile now.
    session = client.get(f"/api/sessions/{sid}").json()
    assert session["status"] == "analyzed"
    assert session["source_profile"] is not None
    assert session["source_profile"]["frameworks"][0]["name"] == "Django"

    # And jobs index returns the same job.
    listing = client.get(f"/api/sessions/{sid}/jobs").json()
    assert any(j["id"] == job_id and j["kind"] == "analyze" for j in listing)


def test_analyze_404_on_missing_session(client: TestClient):
    resp = client.post("/api/sessions/deadbeef/analyze")
    assert resp.status_code == 404
