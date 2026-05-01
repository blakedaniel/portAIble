"""Phase 5: GitHub extraction — public + private (PAT) via async background job.

Hermetic: a fake `git` shim on PATH writes a tiny tree to the destination
directory instead of hitting the network. The extractor only cares that the
subprocess exits 0 and a populated src/ exists.
"""

from __future__ import annotations

import os
import stat
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def fake_git(tmp_path_factory, monkeypatch):
    """Install a `git` shim on PATH ahead of /usr/bin/git.

    The shim parses `git clone ... <dest>`, creates dest/, drops a manage.py
    and requirements.txt into it, and exits 0.
    """
    bin_dir = tmp_path_factory.mktemp("fake-bin")
    git = bin_dir / "git"
    git.write_text(
        "#!/usr/bin/env bash\n"
        "# fake git used by Phase 5 tests\n"
        'if [ "$1" = "clone" ]; then\n'
        '  shift\n'
        '  # last arg is dest dir\n'
        '  dest="${@: -1}"\n'
        '  mkdir -p "$dest"\n'
        '  echo "import django" > "$dest/manage.py"\n'
        '  echo "Django==4.2" > "$dest/requirements.txt"\n'
        '  exit 0\n'
        'fi\n'
        'echo "fake git: unsupported subcommand $1" >&2\n'
        'exit 2\n'
    )
    git.chmod(git.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
    yield bin_dir


@pytest.fixture
def app():
    from portaible.app import app as fastapi_app
    return fastapi_app


@pytest.fixture
def client(app):
    with TestClient(app) as c:
        yield c


def _wait_for_job(client: TestClient, sid: str, jid: str, timeout: float = 5.0) -> dict:
    deadline = time.time() + timeout
    while time.time() < deadline:
        body = client.get(f"/api/sessions/{sid}/jobs/{jid}").json()
        if body["status"] in ("completed", "failed"):
            return body
        time.sleep(0.05)
    pytest.fail(f"job {jid} never finished within {timeout}s")


def test_public_github_clone(client: TestClient, fake_git, _workspace_root: Path):
    sid = client.post("/api/sessions").json()["id"]
    resp = client.post(
        f"/api/sessions/{sid}/source/github",
        json={"url": "https://github.com/example/repo", "kind": "public"},
    )
    assert resp.status_code == 202, resp.text
    job_id = resp.json()["job_id"]

    final = _wait_for_job(client, sid, job_id)
    assert final["status"] == "completed", f"job ended {final['status']}: {final.get('error')}"

    session = client.get(f"/api/sessions/{sid}").json()
    assert session["status"] == "extracted"
    assert session["extraction_kind"] == "github_public"
    assert session["source_uri"] == "https://github.com/example/repo"
    # PAT must NEVER be in the session payload
    assert "pat" not in session and "ghp_" not in str(session)


def test_private_github_requires_pat(client: TestClient, fake_git):
    sid = client.post("/api/sessions").json()["id"]
    resp = client.post(
        f"/api/sessions/{sid}/source/github",
        json={"url": "https://github.com/example/repo", "kind": "private"},
    )
    assert resp.status_code == 400
    assert "personal access token" in resp.text.lower()


def test_private_github_clone_with_pat(client: TestClient, fake_git):
    sid = client.post("/api/sessions").json()["id"]
    resp = client.post(
        f"/api/sessions/{sid}/source/github",
        json={
            "url": "https://github.com/example/private-repo",
            "kind": "private",
            "pat": "ghp_FAKE_TOKEN",
        },
    )
    assert resp.status_code == 202
    final = _wait_for_job(client, sid, resp.json()["job_id"])
    assert final["status"] == "completed"

    session = client.get(f"/api/sessions/{sid}").json()
    assert session["extraction_kind"] == "github_private"
    # PAT NEVER persisted on session
    assert "ghp_FAKE_TOKEN" not in str(session)


def test_invalid_url_rejected(client: TestClient, fake_git):
    sid = client.post("/api/sessions").json()["id"]
    resp = client.post(
        f"/api/sessions/{sid}/source/github",
        json={"url": "https://gitlab.com/foo/bar", "kind": "public"},
    )
    # The job submits 202, then fails inside the background task.
    assert resp.status_code == 202
    final = _wait_for_job(client, sid, resp.json()["job_id"])
    assert final["status"] == "failed"
    assert "github.com" in (final["error"] or "").lower()
