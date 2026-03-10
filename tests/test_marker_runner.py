"""Tests for pdf_markdown.marker_runner utilities."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from pdf_markdown.marker_runner import find_marker_output, run_marker


def test_run_marker_missing_binary(tmp_path: Path, tmp_pdf: Path) -> None:
    """If marker_single is not installed, run_marker returns failure gracefully."""
    with patch(
        "pdf_markdown.marker_runner.subprocess.run",
        side_effect=FileNotFoundError("marker_single"),
    ):
        success, stdout, stderr = run_marker(tmp_pdf, tmp_path)

    assert not success
    assert "marker_single" in stderr.lower() or "not found" in stderr.lower()


def test_run_marker_timeout(tmp_path: Path, tmp_pdf: Path) -> None:
    import subprocess

    with patch(
        "pdf_markdown.marker_runner.subprocess.run",
        side_effect=subprocess.TimeoutExpired(cmd="marker_single", timeout=1),
    ):
        success, stdout, stderr = run_marker(tmp_pdf, tmp_path, timeout=1)

    assert not success
    assert "timed out" in stderr.lower()


def test_find_marker_output_expected_layout(tmp_path: Path) -> None:
    """Marker writes <out>/<stem>/<stem>.md by default."""
    stem = "my_doc"
    expected = tmp_path / stem / f"{stem}.md"
    expected.parent.mkdir(parents=True)
    expected.write_text("# Content")

    found = find_marker_output(tmp_path, stem)
    assert found == expected


def test_find_marker_output_fallback_glob(tmp_path: Path) -> None:
    """Should find any .md in the output dir if canonical path doesn't exist."""
    other = tmp_path / "other_dir" / "result.md"
    other.parent.mkdir(parents=True)
    other.write_text("# Other")

    found = find_marker_output(tmp_path, "stem_that_doesnt_match")
    assert found is not None


def test_find_marker_output_none_when_empty(tmp_path: Path) -> None:
    found = find_marker_output(tmp_path, "nothing")
    assert found is None
