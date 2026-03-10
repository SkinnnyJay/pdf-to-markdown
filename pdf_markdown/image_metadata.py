"""Image metadata — write pdf-markdown metadata to PNG/JPEG for traceability."""

from __future__ import annotations

from pathlib import Path

from pdf_markdown.pdf_markdown_validation import IMAGE_METADATA_KEYS

__all__ = ["write_image_metadata"]


def write_image_metadata(
    img_path: Path,
    *,
    source_file: str,
    md_file: str,
    image_id: str,
) -> None:
    """Write pdf-markdown metadata to an image file for traceability.

    Stores source_file (PDF basename), md_file (Markdown basename), and image_id
    (unique ID matching the placeholder alt text) as PNG tEXt chunks or JPEG
    comments. Overwrites the file in place.

    Args:
        img_path: Path to the PNG or JPEG image.
        source_file: Original PDF filename (e.g. report.pdf).
        md_file: Markdown filename (e.g. report.md).
        image_id: Unique ID matching the placeholder alt (e.g. report-p001).
    """
    try:
        from PIL import Image
        from PIL.PngImagePlugin import PngInfo
    except ImportError:
        return  # Pillow not available

    suffix = img_path.suffix.lower()
    if suffix == ".png":
        meta = PngInfo()
        meta.add_text(IMAGE_METADATA_KEYS["source_file"], source_file)
        meta.add_text(IMAGE_METADATA_KEYS["md_file"], md_file)
        meta.add_text(IMAGE_METADATA_KEYS["image_id"], image_id)

        with Image.open(img_path) as im:
            im.save(img_path, pnginfo=meta)
    elif suffix in (".jpg", ".jpeg"):
        # JPEG: use comment; Pillow supports comment via save(comment=...)
        with Image.open(img_path) as im:
            comment = (
                f"{IMAGE_METADATA_KEYS['source_file']}={source_file};"
                f"{IMAGE_METADATA_KEYS['md_file']}={md_file};"
                f"{IMAGE_METADATA_KEYS['image_id']}={image_id}"
            )
            im.save(img_path, format="JPEG", comment=comment.encode("utf-8"))
