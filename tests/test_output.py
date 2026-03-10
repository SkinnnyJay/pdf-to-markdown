"""Tests for pdf_markdown.output path helpers."""

from __future__ import annotations

from pathlib import Path

from pdf_markdown.output import assets_dir, destination_md, write_markdown


def test_destination_md_basic() -> None:
    root = Path("/out")
    result = destination_md(root, "1880", Path("/src/1880/report.pdf"))
    assert result == Path("/out/1880/report.md")


def test_assets_dir_basic() -> None:
    root = Path("/out")
    result = assets_dir(root, "1880", Path("/src/1880/report.pdf"))
    assert result == Path("/out/1880/report_assets")


def test_write_markdown_creates_file(tmp_path: Path) -> None:
    dest = tmp_path / "1880" / "report.md"
    write_markdown(dest, "# Hello\n")
    assert dest.exists()
    assert dest.read_text(encoding="utf-8") == "# Hello\n"


def test_write_markdown_creates_parents(tmp_path: Path) -> None:
    deep = tmp_path / "a" / "b" / "c" / "file.md"
    write_markdown(deep, "content")
    assert deep.exists()
