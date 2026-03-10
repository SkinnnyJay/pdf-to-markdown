"""Output helpers — write markdown files and return canonical destination paths."""

import shutil
from pathlib import Path

from pdf_markdown.markdown_metadata import embed_metadata
from pdf_markdown.pdf_metadata import get_pdf_metadata

__all__ = ["assets_dir", "copy_marker_output", "destination_md", "write_markdown"]


def destination_md(output_root: Path, group: str, pdf: Path) -> Path:
    """``<output_root>/<group>/<pdf_stem>.md``"""
    return output_root / group / f"{pdf.stem}.md"


def assets_dir(output_root: Path, group: str, pdf: Path) -> Path:
    """``<output_root>/<group>/<pdf_stem>_assets/``"""
    return output_root / group / f"{pdf.stem}_assets"


def write_markdown(dest: Path, content: str) -> None:
    """Write *content* to *dest*, creating parent directories as needed."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(content, encoding="utf-8")


def copy_marker_output(marker_md: Path, dest: Path, pdf: Path) -> None:
    """Copy Marker's .md to *dest* with embedded metadata; copy images/ to <dest_stem>_assets/."""
    dest.parent.mkdir(parents=True, exist_ok=True)

    content = marker_md.read_text(encoding="utf-8")
    metadata = get_pdf_metadata(pdf)
    full_content = embed_metadata(metadata) + content
    write_markdown(dest, full_content)

    marker_img_dir = marker_md.parent / "images"
    if marker_img_dir.is_dir():
        dest_img_dir = dest.parent / f"{dest.stem}_assets"
        shutil.copytree(marker_img_dir, dest_img_dir, dirs_exist_ok=True)
