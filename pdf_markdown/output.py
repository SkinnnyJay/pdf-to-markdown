"""Output helpers — write markdown files and return canonical destination paths."""

import re
import shutil
from pathlib import Path

from pdf_markdown.converters.base import ConverterResult
from pdf_markdown.markdown_metadata import embed_metadata
from pdf_markdown.pdf_metadata import get_pdf_metadata

try:
    from pdf_markdown.image_metadata import write_image_metadata
except ImportError:
    write_image_metadata = None  # type: ignore[assignment]

__all__ = [
    "assets_dir",
    "copy_marker_output",
    "destination_md",
    "write_converter_result",
    "write_markdown",
]


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
    # Marker v1.10+ may write images in same dir as .md
    if not marker_img_dir.is_dir():
        for p in marker_md.parent.iterdir():
            if p.suffix.lower() in (".png", ".jpg", ".jpeg"):
                dest_img_dir = dest.parent / f"{dest.stem}_assets"
                dest_img_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(p, dest_img_dir / p.name)
                break


def write_converter_result(
    result: ConverterResult,
    dest: Path,
    pdf: Path,
    images_src_dir: Path | None,
) -> None:
    """Write ConverterResult to dest, with metadata and optional image copy.

    Copies images from images_src_dir to dest.parent/<stem>_assets/ and rewrites
    image refs in the markdown to use the _assets path.
    """
    dest.parent.mkdir(parents=True, exist_ok=True)
    metadata = get_pdf_metadata(pdf)
    content = result.markdown

    if images_src_dir and images_src_dir.is_dir():
        dest_assets = dest.parent / f"{dest.stem}_assets"
        dest_assets.mkdir(parents=True, exist_ok=True)
        for img in images_src_dir.iterdir():
            if img.suffix.lower() in (".png", ".jpg", ".jpeg"):
                dest_img = dest_assets / img.name
                shutil.copy2(img, dest_img)
                if write_image_metadata:
                    image_id = img.stem
                    write_image_metadata(
                        dest_img,
                        source_file=pdf.name,
                        md_file=dest.name,
                        image_id=image_id,
                    )
        # Rewrite image refs: "image_0.png" -> "stem_assets/image_0.png"
        # Use pdf-markdown:image_id format in alt for traceability
        assets_prefix = f"{dest.stem}_assets/"

        def _rewrite_img(match: re.Match[str]) -> str:
            _, src = match.group(1), match.group(2)
            if src.startswith(assets_prefix) or ":" in src or src.startswith("/"):
                return match.group(0)
            image_id = Path(src).stem
            new_alt = f"pdf-markdown:{image_id}"
            return f"![{new_alt}]({assets_prefix}{src})"

        content = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", _rewrite_img, content)

    full_content = embed_metadata(metadata) + content
    write_markdown(dest, full_content)
