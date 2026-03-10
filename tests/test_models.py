"""Tests for pdf_markdown.models."""

from __future__ import annotations

from pathlib import Path

from pdf_markdown.models import ConversionResult


def test_defaults() -> None:
    r = ConversionResult(pdf=Path("a.pdf"), group="1880", success=True)
    assert r.output_md is None
    assert r.stdout == ""
    assert r.stderr == ""
    assert r.error == ""
    assert r.extracted_images == []


def test_extracted_images_not_shared() -> None:
    """Mutable default must not be shared between instances."""
    r1 = ConversionResult(pdf=Path("a.pdf"), group="g", success=False)
    r2 = ConversionResult(pdf=Path("b.pdf"), group="g", success=False)
    r1.extracted_images.append(Path("x.png"))
    assert r2.extracted_images == []


def test_success_fields() -> None:
    dest = Path("transformed/1880/report.md")
    r = ConversionResult(
        pdf=Path("1880/report.pdf"),
        group="1880",
        success=True,
        output_md=dest,
        stdout="ok",
    )
    assert r.success is True
    assert r.output_md == dest
    assert r.stdout == "ok"
