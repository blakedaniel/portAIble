"""SourcePicker — verifies priority manifests come first and budgets are honored."""

from __future__ import annotations

from pathlib import Path

from portaible.infrastructure.llm.source_picker import list_files, pick_representative


def test_priority_files_picked_first(tmp_path: Path):
    (tmp_path / "requirements.txt").write_text("Django==4.2\n")
    (tmp_path / "README.md").write_text("# project\n")
    (tmp_path / "myapp").mkdir()
    (tmp_path / "myapp" / "models.py").write_text("from django.db import models\n")
    (tmp_path / "myapp" / "views.py").write_text("from django.shortcuts import render\n")
    # Noise
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "junk.js").write_text("ignore me")

    files = list_files(tmp_path)
    assert "node_modules/junk.js" not in files  # pruned

    picks = pick_representative(tmp_path, max_files=10, max_file_bytes=1000)
    paths = [p for p, _ in picks]
    # Priority manifest + README must appear first
    assert "requirements.txt" in paths[:2]
    assert "README.md" in paths[:3]


def test_byte_cap_truncates(tmp_path: Path):
    big = "x" * 5000
    (tmp_path / "huge.py").write_text(big)

    picks = pick_representative(tmp_path, max_files=5, max_file_bytes=1000)
    assert len(picks) == 1
    _, content = picks[0]
    assert len(content) < 1500  # truncated + suffix
    assert "[truncated" in content
