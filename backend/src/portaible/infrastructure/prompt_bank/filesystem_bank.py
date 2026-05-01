"""Filesystem-backed PromptBankPort — reads markdown from prompt-bank/ subdirs."""

from __future__ import annotations

import logging
import re
from pathlib import Path

from ...ports import PromptBankPort

logger = logging.getLogger(__name__)


def _slugify(name: str) -> str:
    """Normalize a free-form name to a filesystem-safe slug.

    Decimal versions (containing a dot) are stripped — they don't differentiate bank docs.
    Bare major-version digits are kept — they DO differentiate (e.g. Nuxt 2 vs Nuxt 4,
    Vue 2 vs Vue 3, Python 2 vs Python 3).

    Examples:
        'Spring Boot 3.5'  -> 'springboot'   (decimal version stripped)
        'Python 3.11'      -> 'python'       (decimal version stripped)
        'FastAPI 0.110'    -> 'fastapi'      (decimal version stripped)
        'Nuxt 2'           -> 'nuxt2'        (bare major version kept)
        'Vue 3'            -> 'vue3'
        'C#'               -> 'csharp'       (special-cased)
        'C++'              -> 'cpp'
        '.NET'             -> 'dotnet'
    """
    s = name.lower().strip()
    s = s.replace("c#", "csharp").replace("c++", "cpp").replace(".net", "dotnet")
    # Strip decimal versions (X.Y or X.Y.Z) wherever they appear, before alphanumeric squash.
    s = re.sub(r"\d+\.\d+(\.\d+)*", "", s)
    s = re.sub(r"\s+", "", s)            # drop whitespace
    s = re.sub(r"[^a-z0-9]", "", s)      # keep only alphanumerics
    return s


class FilesystemPromptBank(PromptBankPort):
    def __init__(self, root: Path | str):
        self.root = Path(root)

    def fetch_language_doc(self, name: str) -> str | None:
        return self._read("languages", _slugify(name))

    def fetch_framework_doc(self, name: str) -> str | None:
        return self._read("frameworks", _slugify(name))

    def fetch_transition_doc(self, src_framework: str, dst_framework: str) -> str | None:
        slug = f"{_slugify(src_framework)}-{_slugify(dst_framework)}"
        return self._read("transitions", slug)

    def index(self) -> dict[str, list[str]]:
        return {
            "languages": self._list("languages"),
            "frameworks": self._list("frameworks"),
            "transitions": self._list("transitions"),
        }

    def _read(self, subdir: str, slug: str) -> str | None:
        if not slug:
            return None
        path = self.root / subdir / f"{slug}.md"
        if not path.is_file():
            logger.debug("[prompt-bank] miss: %s", path)
            return None
        return path.read_text(encoding="utf-8")

    def _list(self, subdir: str) -> list[str]:
        d = self.root / subdir
        if not d.is_dir():
            return []
        return sorted(p.stem for p in d.glob("*.md") if p.stem.lower() != "readme")
