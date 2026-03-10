"""Fallback image extraction — rasterise PDF pages when Marker conversion fails."""

from pathlib import Path

try:
    import fitz  # pymupdf
except ImportError:
    fitz = None  # type: ignore[assignment]


def extract_images(
    pdf: Path,
    assets_dir: Path,
    *,
    dpi: int = 150,
) -> list[Path]:
    """Rasterise every page of *pdf* to PNG files inside *assets_dir*.

    Uses ``pymupdf`` (fitz) which is bundled as a dependency. Each page is
    saved as ``<stem>-p<N>.png`` (1-indexed).

    Args:
        pdf: Source PDF path.
        assets_dir: Directory where PNG files will be written.
        dpi: Render resolution (150 dpi is a reasonable OCR-readable size).

    Returns:
        List of paths to the created PNG files.
    """
    if fitz is None:
        raise RuntimeError(
            "pymupdf is required for image extraction. Install with: pip install pymupdf",
        )

    assets_dir.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(str(pdf))
    mat = fitz.Matrix(dpi / 72, dpi / 72)

    images: list[Path] = []
    for page_num, page in enumerate(doc, start=1):
        pix = page.get_pixmap(matrix=mat, alpha=False)
        img_path = assets_dir / f"{pdf.stem}-p{page_num:03d}.png"
        pix.save(str(img_path))
        images.append(img_path)

    doc.close()
    return images


def generate_placeholder_markdown(
    pdf: Path,
    assets_dir: Path,
    images: list[Path],
    error_msg: str,
) -> str:
    """Build a Markdown string that documents the failure and embeds image links.

    Args:
        pdf: Original PDF path.
        assets_dir: Directory containing the extracted images.
        images: Ordered list of extracted image paths.
        error_msg: Human-readable description of why conversion failed.

    Returns:
        Markdown string ready to write to a ``.md`` file.
    """
    lines: list[str] = [
        f"# {pdf.stem}",
        "",
        "> **Note:** Automatic Markdown conversion failed for this file.",
        f"> Reason: `{error_msg}`",
        ">",
        "> Page images have been extracted and are embedded below.",
        "",
        "---",
        "",
    ]

    for img in images:
        rel = img.relative_to(assets_dir.parent)
        lines.append(f"![{img.name}]({rel})")
        lines.append("")

    if not images:
        lines.append("_No pages could be extracted from this PDF._")
        lines.append("")

    return "\n".join(lines)
