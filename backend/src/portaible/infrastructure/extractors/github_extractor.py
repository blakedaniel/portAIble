"""GitHub source extractor — shallow-clones a public or PAT-authenticated repo.

PATs are used only for the duration of a single clone subprocess and are
embedded in the URL passed via stdin-ish env (`GIT_ASKPASS`-style would be safer
but more setup; for local single-user we accept URL-embedding with redaction in
logs). PATs are NEVER persisted on the Session.
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
import shutil
from pathlib import Path
from typing import BinaryIO
from urllib.parse import urlparse, urlunparse

from ...config import settings
from ...domain import ExtractionKind
from ...ports import ExtractionResult, SourceExtractorPort

logger = logging.getLogger(__name__)


_GITHUB_HOSTS = {"github.com", "www.github.com"}


def _validate_github_url(url: str) -> str:
    """Reject anything that doesn't look like a github.com repo URL.

    Accepted shapes (returned normalized to https://github.com/<owner>/<repo>):
      - https://github.com/owner/repo
      - https://github.com/owner/repo.git
      - http://github.com/owner/repo (upgraded to https)
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"GitHub URL must be http(s): {url}")
    if parsed.hostname not in _GITHUB_HOSTS:
        raise ValueError(f"only github.com URLs are accepted: {url}")
    path = parsed.path.lstrip("/").removesuffix(".git")
    parts = [p for p in path.split("/") if p]
    if len(parts) < 2:
        raise ValueError(f"GitHub URL must include owner/repo: {url}")
    return f"https://github.com/{parts[0]}/{parts[1]}"


def _embed_pat(url: str, pat: str) -> str:
    """Return URL with PAT embedded as basic auth user. Never log this value."""
    parsed = urlparse(url)
    netloc = f"{pat}:x-oauth-basic@{parsed.hostname}"
    if parsed.port:
        netloc = f"{netloc}:{parsed.port}"
    return urlunparse(parsed._replace(netloc=netloc))


_PAT_REDACTOR = re.compile(r"https://[^@\s]+@")


def _redact(s: str) -> str:
    return _PAT_REDACTOR.sub("https://<redacted>@", s)


class GithubSourceExtractor(SourceExtractorPort):
    """Handles BOTH public and private (PAT) clones — `kind` is set per call.

    Registered twice in `get_extractors`, once for each ExtractionKind, so
    callers retain symmetry with the ZIP adapter.
    """

    def __init__(self, kind: ExtractionKind, workspace_root: Path | None = None,
                  depth: int | None = None):
        if kind not in (ExtractionKind.GITHUB_PUBLIC, ExtractionKind.GITHUB_PRIVATE):
            raise ValueError(f"GithubSourceExtractor cannot handle kind={kind!r}")
        self.kind = kind
        self.workspace_root = workspace_root or Path(settings.workspace_dir)
        self.depth = depth or settings.github_clone_depth

    async def extract_zip(self, *, session_id: str, file: BinaryIO) -> ExtractionResult:
        raise NotImplementedError("GithubSourceExtractor does not support ZIP extraction")

    async def extract_github(
        self,
        *,
        session_id: str,
        url: str,
        ref: str | None = None,
        pat: str | None = None,
    ) -> ExtractionResult:
        normalized = _validate_github_url(url)
        if self.kind is ExtractionKind.GITHUB_PRIVATE and not pat:
            raise ValueError("private GitHub extraction requires a PAT")

        clone_url = _embed_pat(normalized, pat) if pat else normalized

        session_dir = self.workspace_root / "sessions" / session_id
        src_dir = session_dir / "src"
        if src_dir.exists():
            shutil.rmtree(src_dir)
        src_dir.parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            "git", "clone",
            "--depth", str(self.depth),
            "--single-branch",
        ]
        if ref:
            cmd += ["--branch", ref]
        cmd += [clone_url, str(src_dir)]

        logger.info("[github-extract] session=%s url=%s ref=%s", session_id, normalized, ref or "HEAD")

        env = os.environ.copy()
        env["GIT_TERMINAL_PROMPT"] = "0"  # never prompt for credentials
        env["GIT_LFS_SKIP_SMUDGE"] = "1"

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            env=env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            err = _redact((stderr.decode("utf-8", errors="replace") or "git clone failed").strip())
            raise RuntimeError(f"git clone failed (exit {proc.returncode}): {err}")

        # Strip the .git directory — we don't ship it through the AI pipeline.
        git_dir = src_dir / ".git"
        if git_dir.is_dir():
            shutil.rmtree(git_dir, ignore_errors=True)

        file_count = 0
        listing: list[str] = []
        for dirpath, _, filenames in os.walk(src_dir):
            for fname in filenames:
                if fname.startswith("._") or fname == ".DS_Store":
                    continue
                full = Path(dirpath) / fname
                rel = full.relative_to(src_dir)
                if file_count < 50:
                    listing.append(str(rel))
                file_count += 1

        logger.info("[github-extract] session=%s files=%d dest=%s", session_id, file_count, src_dir)
        return ExtractionResult(
            workspace_src_dir=src_dir,
            file_count=file_count,
            top_level_listing=sorted(listing),
            extraction_kind=self.kind,
            source_uri=normalized,
        )
