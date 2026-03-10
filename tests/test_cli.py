"""Tests for the pdf-markdown CLI (Typer + Rich) via typer.testing."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from pdf_markdown.cli import app

runner = CliRunner()


def test_version_flag() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "pdf-markdown" in result.output


def test_convert_no_args_exits_nonzero() -> None:
    result = runner.invoke(app, ["convert"])
    assert result.exit_code != 0


def test_dry_run_shows_table(tmp_path: Path) -> None:
    group_dir = tmp_path / "1880"
    group_dir.mkdir()
    (group_dir / "report.pdf").write_bytes(b"%PDF-1.4\n%%EOF\n")

    result = runner.invoke(
        app,
        [
            "convert",
            "--source",
            str(tmp_path),
            "--output",
            str(tmp_path / "out"),
            "--dry-run",
        ],
    )
    assert result.exit_code == 0
    # Rich may truncate long paths; check for the file stem at minimum
    assert "report" in result.output


def test_dry_run_with_groups(tmp_path: Path) -> None:
    for yr in ("1880", "1890"):
        d = tmp_path / yr
        d.mkdir()
        (d / f"{yr}.pdf").write_bytes(b"%PDF\n%%EOF\n")

    result = runner.invoke(
        app,
        [
            "convert",
            "--source",
            str(tmp_path),
            "--groups",
            "1880",
            "--output",
            str(tmp_path / "out"),
            "--dry-run",
        ],
    )
    assert result.exit_code == 0
    assert "1880" in result.output
    # 1890 was excluded by --groups; it should not appear as a group row
    assert result.output.count("1890") == 0


def test_convert_explicit_input_dry_run(tmp_path: Path, tmp_pdf: Path) -> None:
    result = runner.invoke(
        app,
        [
            "convert",
            "--input",
            str(tmp_pdf),
            "--output",
            str(tmp_path / "out"),
            "--dry-run",
        ],
    )
    assert result.exit_code == 0
    # Rich may truncate long absolute paths; check for stem
    assert "sample" in result.output


def _make_failed_marker(stdout: str = "", stderr: str = "Marker failed") -> MagicMock:
    m = MagicMock(return_value=(False, stdout, stderr))
    return m


def test_convert_uses_fallback_on_marker_failure(
    tmp_path: Path,
    tmp_pdf: Path,
) -> None:
    output_dir = tmp_path / "out"

    with (
        patch("pdf_markdown.cli.run_marker", return_value=(False, "", "marker error")),
        patch(
            "pdf_markdown.cli.extract_images",
            return_value=[],
        ),
    ):
        result = runner.invoke(
            app,
            [
                "convert",
                "--input",
                str(tmp_pdf),
                "--output",
                str(output_dir),
            ],
        )

    assert result.exit_code == 1  # failures return 1
    dest = output_dir / tmp_path.name / "sample.md"
    assert dest.exists()
    content = dest.read_text()
    assert "# sample" in content


# ── validate subcommand ───────────────────────────────────────────────────────


def test_validate_clean_output(tmp_path: Path) -> None:
    group_dir = tmp_path / "1880"
    group_dir.mkdir()
    (group_dir / "report.md").write_text("# Report\n\nContent.", encoding="utf-8")

    result = runner.invoke(app, ["validate", "--output", str(tmp_path)])
    assert result.exit_code == 0


def test_validate_detects_empty_file(tmp_path: Path) -> None:
    group_dir = tmp_path / "1880"
    group_dir.mkdir()
    (group_dir / "empty.md").write_text("  ", encoding="utf-8")

    result = runner.invoke(app, ["validate", "--output", str(tmp_path)])
    assert result.exit_code == 1


def test_validate_strict_missing_image_fails(tmp_path: Path) -> None:
    group_dir = tmp_path / "1880"
    group_dir.mkdir()
    (group_dir / "doc.md").write_text("![x](missing.png)\n", encoding="utf-8")

    result = runner.invoke(app, ["validate", "--output", str(tmp_path), "--strict"])
    assert result.exit_code == 1


def test_validate_non_strict_missing_image_passes(tmp_path: Path) -> None:
    group_dir = tmp_path / "1880"
    group_dir.mkdir()
    (group_dir / "doc.md").write_text("![x](missing.png)\n", encoding="utf-8")

    result = runner.invoke(app, ["validate", "--output", str(tmp_path)])
    # Warnings alone should not fail the command
    assert result.exit_code == 0
