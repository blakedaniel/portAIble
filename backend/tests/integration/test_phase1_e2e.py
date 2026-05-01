"""Phase 1 end-to-end: create → upload zip → analyze → confirm → suggest dest → confirm → build → submit (mocked) → poll → fetch."""

from __future__ import annotations

import io
import zipfile
from pathlib import Path

import httpx
import pytest
import respx
from fastapi.testclient import TestClient


@pytest.fixture
def app():
    # Import inside the fixture so conftest env vars apply first.
    from portaible.app import app as fastapi_app
    return fastapi_app


@pytest.fixture
def client(app):
    with TestClient(app) as c:
        yield c


def _make_django_zip() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("manage.py", "#!/usr/bin/env python\nimport os, sys\n")
        z.writestr("requirements.txt", "Django==4.2\ndjangorestframework==3.14\n")
        z.writestr("myapp/__init__.py", "")
        z.writestr("myapp/models.py", "from django.db import models\n")
        z.writestr("myapp/views.py", "from django.shortcuts import render\n")
    return buf.getvalue()


def test_full_phase1_flow(client: TestClient, _workspace_root: Path):
    # 1. Create session
    resp = client.post("/api/sessions")
    assert resp.status_code == 201, resp.text
    sid = resp.json()["id"]

    # 2. Upload zip
    zip_bytes = _make_django_zip()
    resp = client.post(
        f"/api/sessions/{sid}/source/zip",
        files={"file": ("django-app.zip", zip_bytes, "application/zip")},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "extracted"
    assert resp.json()["extracted_file_count"] == 5

    src_dir = _workspace_root / "sessions" / sid / "src"
    assert (src_dir / "manage.py").exists()
    assert (src_dir / "myapp" / "models.py").exists()

    # 3. Analyze synchronously (background flow has its own test).
    resp = client.post(f"/api/sessions/{sid}/analyze/sync")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "analyzed"
    assert body["source_profile"]["frameworks"][0]["name"] == "Django"

    # 4. Edit profile (add a package) + confirm
    profile = body["source_profile"]
    profile["packages"].append({"name": "celery", "version": "5.3", "alternatives": []})
    resp = client.put(f"/api/sessions/{sid}/profiles/source", json=profile)
    assert resp.status_code == 200
    resp = client.post(f"/api/sessions/{sid}/profiles/source/confirm")
    assert resp.status_code == 200
    assert resp.json()["status"] == "source_profile_confirmed"

    # 5. Suggest destination + confirm
    resp = client.post(
        f"/api/sessions/{sid}/profiles/destination/suggest",
        json={"target_hint": "Spring Boot 3.5"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["destination_profile"]["frameworks"][0]["name"] == "Spring Boot"
    resp = client.post(f"/api/sessions/{sid}/profiles/destination/confirm")
    assert resp.status_code == 200
    assert resp.json()["status"] == "destination_profile_confirmed"

    # 6. Build prompt (skip decisions in Phase 1)
    resp = client.post(f"/api/sessions/{sid}/prompt/build")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "prompt_built"
    assert body["assembled_prompt"]["instructions"]
    instr = body["assembled_prompt"]["instructions"]
    # The bank should have spliced in matching docs:
    assert "Django" in instr
    assert "Spring Boot" in instr
    assert "Component mapping" in instr  # from transitions/django-springboot.md

    # 7. Mock the AI Pipeline upstream and submit
    with respx.mock(base_url="http://test-ai-pipeline.local") as mock:
        mock.post("/chat").mock(return_value=httpx.Response(200, json={"job_id": "abc123"}))
        mock.get("/chat/jobs/abc123").mock(
            return_value=httpx.Response(
                200,
                json={
                    "job_id": "abc123",
                    "status": "completed",
                    "progress_percentage": 100,
                    "progress_message": "Done",
                    "error": None,
                },
            )
        )
        mock.get("/chat/jobs/abc123/result").mock(
            return_value=httpx.Response(
                200,
                content=b"#!/bin/bash\necho 'ported app'\n",
                headers={"content-type": "application/x-shellscript"},
            )
        )

        resp = client.post(f"/api/sessions/{sid}/pipeline/submit")
        assert resp.status_code == 200, resp.text
        assert resp.json()["status"] == "pipeline_submitted"
        assert resp.json()["pipeline_remote_job_id"] == "abc123"

        resp = client.get(f"/api/sessions/{sid}/pipeline/status")
        assert resp.status_code == 200
        assert resp.json()["status"] == "completed"

        resp = client.get(f"/api/sessions/{sid}/pipeline/result")
        assert resp.status_code == 200
        assert resp.content == b"#!/bin/bash\necho 'ported app'\n"

    # 8. Verify session is in terminal state
    resp = client.get(f"/api/sessions/{sid}")
    assert resp.json()["status"] == "pipeline_completed"
