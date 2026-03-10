"""Tests for pdf_markdown.pdf_metadata."""

from pathlib import Path

from pdf_markdown.pdf_metadata import get_pdf_metadata


def test_get_pdf_metadata_always_includes_source_file(tmp_path: Path) -> None:
    pdf = tmp_path / "nonexistent.pdf"
    # Even for missing file, we return source_file (PyMuPDF may fail to open)
    result = get_pdf_metadata(pdf)
    assert result["source_file"] == "nonexistent.pdf"


def test_get_pdf_metadata_with_real_pdf(tmp_path: Path) -> None:
    # Create a minimal valid PDF using PyMuPDF if available
    try:
        import fitz
    except ImportError:
        return

    pdf = tmp_path / "test.pdf"
    doc = fitz.open()
    doc.insert_page(0, width=100, height=100)
    doc.set_metadata({"author": "Test Author", "title": "Test Title"})
    doc.save(str(pdf))
    doc.close()

    result = get_pdf_metadata(pdf)
    assert result["source_file"] == "test.pdf"
    assert result.get("author") == "Test Author"
    assert result.get("title") == "Test Title"
