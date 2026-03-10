"""Tests for pdf_markdown.fallback_images — placeholder generation."""

from __future__ import annotations

from pathlib import Path

from pdf_markdown.fallback_images import generate_placeholder_markdown


def test_placeholder_contains_heading(tmp_path: Path) -> None:
    pdf = tmp_path / "old_doc.pdf"
    a_dir = tmp_path / "old_doc_assets"
    md = generate_placeholder_markdown(pdf, a_dir, [], "Marker crashed")
    assert "# old_doc" in md


def test_placeholder_contains_error(tmp_path: Path) -> None:
    pdf = tmp_path / "file.pdf"
    a_dir = tmp_path / "file_assets"
    md = generate_placeholder_markdown(pdf, a_dir, [], "timeout after 600s")
    assert "timeout after 600s" in md


def test_placeholder_embeds_image_links(tmp_path: Path) -> None:
    pdf = tmp_path / "scan.pdf"
    a_dir = tmp_path / "scan_assets"
    a_dir.mkdir()
    imgs = [a_dir / "scan-p001.png", a_dir / "scan-p002.png"]
    for img in imgs:
        img.write_bytes(b"")

    md = generate_placeholder_markdown(pdf, a_dir, imgs, "err")
    assert "scan-p001.png" in md
    assert "scan-p002.png" in md


def test_placeholder_no_images_message(tmp_path: Path) -> None:
    pdf = tmp_path / "x.pdf"
    a_dir = tmp_path / "x_assets"
    md = generate_placeholder_markdown(pdf, a_dir, [], "err")
    assert "No pages could be extracted" in md
