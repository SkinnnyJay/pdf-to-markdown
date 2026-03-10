"""Output helpers — write markdown files and return canonical destination paths."""

from __future__ import annotations

import shutil
from pathlib import Path

__all__ = ["assets_dir", "copy_marker_output", "destination_md", "write_markdown"]


def destination_md(output_root: Path, group: str, pdf: Path) -> Path:
    """Return the canonical output path for a converted PDF.

    Layout: ``<output_root>/<group>/<pdf_stem>.md``

    Args:
        output_root: Root output directory (e.g. ``./transformed``).
        group: Group/year name (e.g. ``"1880"``).
        pdf: Source PDF path; its stem is used as the file name.

    Returns:
        Full path to the target ``.md`` file.
    """
    return output_root / group / f"{pdf.stem}.md"


def assets_dir(output_root: Path, group: str, pdf: Path) -> Path:
    """Return the canonical assets directory path for a PDF.

    Layout: ``<output_root>/<group>/<pdf_stem>_assets/``

    Args:
        output_root: Root output directory.
        group: Group/year name.
        pdf: Source PDF path.

    Returns:
        Full path to the assets directory.
    """
    return output_root / group / f"{pdf.stem}_assets"


def write_markdown(dest: Path, content: str) -> None:
    """Write *content* to *dest*, creating parent directories as needed.

    Args:
        dest: Target ``.md`` path.
        content: Markdown text to write.
    """
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(content, encoding="utf-8")


def copy_marker_output(marker_md: Path, dest: Path) -> None:
    """Copy the markdown Marker produced to the canonical destination.

    Also copies any sibling ``images/`` directory that Marker created, renaming
    it to ``<dest_stem>_assets/`` to follow the package convention.

    Args:
        marker_md: Path to Marker's generated ``.md`` file.
        dest: Canonical destination ``.md`` path.
    """
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(marker_md, dest)

    marker_img_dir = marker_md.parent / "images"
    if marker_img_dir.is_dir():
        dest_img_dir = dest.parent / f"{dest.stem}_assets"
        shutil.copytree(marker_img_dir, dest_img_dir, dirs_exist_ok=True)
