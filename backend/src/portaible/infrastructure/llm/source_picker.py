"""Pick a bounded set of representative files from an extracted source dir.

Strategy: always include known dependency manifests + READMEs (high signal),
then sample source files by extension up to a cap, capping each file's bytes
so the LLM context isn't blown.
"""

from __future__ import annotations

import os
from pathlib import Path

# Highest-signal files — always pulled when present.
_PRIORITY_FILES = frozenset({
    "requirements.txt", "pyproject.toml", "setup.py", "setup.cfg", "Pipfile",
    "package.json", "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
    "pom.xml", "build.gradle", "build.gradle.kts", "settings.gradle", "settings.gradle.kts",
    "Cargo.toml", "go.mod", "go.sum",
    "Gemfile", "Gemfile.lock",
    "composer.json",
    "Dockerfile", "docker-compose.yml", "docker-compose.yaml",
    "tsconfig.json", "nuxt.config.ts", "nuxt.config.js",
    "manage.py", "wsgi.py", "asgi.py",
    "README.md", "README.rst", "README", "README.txt",
})

# Extensions worth sampling when no priority manifest is found.
_SOURCE_EXTENSIONS = (
    ".py", ".js", ".ts", ".tsx", ".jsx", ".vue", ".svelte",
    ".java", ".kt", ".scala",
    ".go", ".rs", ".rb", ".php", ".cs",
    ".cpp", ".c", ".h",
)


def list_files(src_dir: Path) -> list[str]:
    out: list[str] = []
    for dirpath, dirnames, filenames in os.walk(src_dir):
        # Prune obvious noise dirs to keep the listing readable.
        dirnames[:] = [
            d for d in dirnames
            if d not in {"node_modules", ".git", ".venv", "__pycache__", "target", "build", "dist"}
        ]
        for fname in filenames:
            if fname.startswith("._") or fname == ".DS_Store":
                continue
            full = Path(dirpath) / fname
            try:
                rel = full.relative_to(src_dir)
            except ValueError:
                continue
            out.append(str(rel))
    return sorted(out)


def pick_representative(
    src_dir: Path,
    *,
    max_files: int,
    max_file_bytes: int,
) -> list[tuple[str, str]]:
    """Return a list of (relative_path, truncated_content) tuples capped at *max_files*.

    Priority manifests always come first; the rest is filled by sampling source files
    deterministically (sorted by path).
    """
    all_files = list_files(src_dir)

    priority: list[str] = []
    sources: list[str] = []
    for rel in all_files:
        name = os.path.basename(rel)
        if name in _PRIORITY_FILES:
            priority.append(rel)
        elif rel.lower().endswith(_SOURCE_EXTENSIONS):
            sources.append(rel)

    picked = priority[:max_files] + sources[: max(0, max_files - len(priority))]
    out: list[tuple[str, str]] = []
    for rel in picked:
        full = src_dir / rel
        try:
            content = full.read_text(encoding="utf-8", errors="replace")
        except (OSError, UnicodeDecodeError):
            continue
        if len(content) > max_file_bytes:
            content = content[:max_file_bytes] + f"\n... [truncated, {len(content)} bytes total]\n"
        out.append((rel, content))
    return out
