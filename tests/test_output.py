"""Tests for pdf_markdown.output path helpers."""

from pathlib import Path

from pdf_markdown.output import assets_dir, copy_marker_output, destination_md, write_markdown


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


def test_copy_marker_output_embeds_metadata(tmp_path: Path, tmp_pdf: Path) -> None:
    marker_dir = tmp_path / "marker_out"
    marker_dir.mkdir()
    marker_md = marker_dir / "sample.md"
    marker_md.write_text("# Sample\n\nBody.", encoding="utf-8")

    dest = tmp_path / "out" / "sample.md"
    copy_marker_output(marker_md, dest, tmp_pdf)

    assert dest.exists()
    content = dest.read_text()
    assert "pdf-markdown:metadata" in content
    assert "sample.pdf" in content
    assert "# Sample" in content
