"""PDF→Markdown validation — static functions for PDF, Markdown, and image validation.

These functions can be used by pdf-markdown and markdowns-concatenation to validate
input and output of the PDF→Markdown pipeline.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Literal, TypedDict

__all__ = [
    "ValidationIssue",
    "IMAGE_METADATA_KEYS",
    "validate_pdf",
    "validate_markdown",
    "validate_images",
    "validate_single_file",
    "validate_output_tree",
]

# Metadata keys written to images to tie them back to PDF/Markdown (PNG tEXt chunks).
IMAGE_METADATA_KEYS = {
    "source_file": "pdf-markdown:source_file",  # original PDF basename
    "md_file": "pdf-markdown:md_file",  # markdown file basename
    "image_id": "pdf-markdown:image_id",  # unique id matching placeholder alt text
}

# Alt text format for image placeholders with unique ID: ![pdf-markdown:image-id](path)
_IMAGE_ID_ALT_PREFIX = "pdf-markdown:"
_IMAGE_REF_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")


class ValidationIssue(TypedDict):
    """A single validation finding."""

    severity: Literal["error", "warning"]
    file: str
    message: str


def validate_pdf(pdf_path: Path) -> list[ValidationIssue]:
    """Validate that a PDF file is valid and readable.

    Checks performed:
    * File exists.
    * File can be opened as a PDF.
    * PDF has at least one page.

    Args:
        pdf_path: Path to the PDF file.

    Returns:
        List of ValidationIssue dicts; empty means the PDF is valid.
    """
    issues: list[ValidationIssue] = []
    rel = str(pdf_path)

    if not pdf_path.exists():
        issues.append({"severity": "error", "file": rel, "message": "PDF file does not exist."})
        return issues

    if not pdf_path.is_file():
        issues.append({"severity": "error", "file": rel, "message": "Path is not a file."})
        return issues

    try:
        import fitz  # pymupdf
    except ImportError:
        issues.append(
            {
                "severity": "error",
                "file": rel,
                "message": "pymupdf required for PDF validation. pip install pymupdf",
            }
        )
        return issues

    try:
        doc = fitz.open(str(pdf_path))
        page_count = len(doc)
        doc.close()
        if page_count < 1:
            issues.append({"severity": "error", "file": rel, "message": "PDF has no pages."})
    except Exception as exc:
        issues.append(
            {
                "severity": "error",
                "file": rel,
                "message": f"PDF is invalid or corrupted: {exc!s}",
            }
        )

    return issues


def validate_markdown(
    md_path: Path | None = None,
    *,
    content: str | None = None,
) -> list[ValidationIssue]:
    """Validate that Markdown content is valid and well-formed.

    Checks performed:
    * Content is non-empty (or file exists and is non-empty).
    * Content is valid UTF-8.
    * Content parses as valid Markdown (via markdown-it-py).

    Args:
        md_path: Path to the Markdown file (for error reporting). Optional if content given.
        content: Markdown content to validate. If None, reads from md_path.

    Returns:
        List of ValidationIssue dicts; empty means the Markdown is valid.
    """
    issues: list[ValidationIssue] = []
    rel = str(md_path) if md_path else "(inline content)"

    if content is None:
        if md_path is None:
            issues.append(
                {
                    "severity": "error",
                    "file": rel,
                    "message": "Either md_path or content must be provided.",
                }
            )
            return issues
        try:
            content = md_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            issues.append({"severity": "error", "file": rel, "message": "File is not valid UTF-8."})
            return issues
        except OSError as exc:
            issues.append(
                {"severity": "error", "file": rel, "message": f"Cannot read file: {exc!s}"}
            )
            return issues

    if not content.strip():
        issues.append({"severity": "error", "file": rel, "message": "Markdown content is empty."})
        return issues

    try:
        from markdown_it import MarkdownIt

        md = MarkdownIt()
        md.parse(content)
    except ImportError:
        issues.append(
            {
                "severity": "warning",
                "file": rel,
                "message": "markdown-it-py not installed; skipping parse validation.",
            }
        )
    except Exception as exc:
        issues.append(
            {
                "severity": "error",
                "file": rel,
                "message": f"Markdown parse error: {exc!s}",
            }
        )

    return issues


def _get_image_metadata(img_path: Path) -> dict[str, str]:
    """Read pdf-markdown metadata from a PNG/JPEG image if present."""
    result: dict[str, str] = {}
    try:
        from PIL import Image

        with Image.open(img_path) as im:
            # PNG: tEXt chunks in im.info
            if hasattr(im, "info") and im.info:
                for key, val in im.info.items():
                    if isinstance(key, str) and key.startswith("pdf-markdown:"):
                        result[key] = str(val) if val else ""
            # JPEG: comment with format "pdf-markdown:source_file=x;pdf-markdown:md_file=y;..."
            if hasattr(im, "comment") and im.comment:
                comment = im.comment.decode("utf-8", errors="replace")
                for part in comment.split(";"):
                    if "=" in part and "pdf-markdown:" in part:
                        k, _, v = part.partition("=")
                        result[k.strip()] = v.strip()
    except Exception:
        pass
    return result


def validate_images(
    md_path: Path,
    *,
    strict: bool = False,
    check_metadata: bool = True,
) -> list[ValidationIssue]:
    """Validate images referenced in a Markdown file.

    Checks performed:
    * Every ``![alt](path)`` image reference resolves to an existing file.
    * Each image file can be opened as a valid image.
    * (check_metadata) If image has pdf-markdown metadata, verify it ties back to
      the markdown (source_file, md_file, image_id match expected values).
    * (strict) Missing image references are errors instead of warnings.

    Args:
        md_path: Path to the Markdown file.
        strict: When True, broken image references are errors.
        check_metadata: When True, validate image metadata ties back to markdown.

    Returns:
        List of ValidationIssue dicts; empty means all images are valid.
    """
    issues: list[ValidationIssue] = []
    rel = str(md_path)

    try:
        content = md_path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return issues  # Let validate_markdown handle read errors

    expected_source = md_path.with_suffix(".pdf").name

    for match in _IMAGE_REF_RE.finditer(content):
        alt_text, img_ref = match.group(1), match.group(2)
        if img_ref.startswith(("http://", "https://", "data:")):
            continue

        img_path = (md_path.parent / img_ref).resolve()
        if not img_path.exists():
            severity: Literal["error", "warning"] = "error" if strict else "warning"
            issues.append(
                {
                    "severity": severity,
                    "file": rel,
                    "message": f"Missing image reference: {img_ref}",
                }
            )
            continue

        # Validate image can be opened and is not corrupted
        try:
            from PIL import Image

            with Image.open(img_path) as im:
                im.load()  # Force decode; raises if corrupted
        except ImportError:
            pass  # Pillow not available, skip image format check
        except Exception as exc:
            issues.append(
                {
                    "severity": "error",
                    "file": rel,
                    "message": f"Invalid or corrupted image: {img_ref} — {exc!s}",
                }
            )
            continue

        # Check metadata ties back to markdown
        if check_metadata:
            meta = _get_image_metadata(img_path)
            if meta:
                # Has our metadata — validate consistency
                src = meta.get(IMAGE_METADATA_KEYS["source_file"], "")
                md = meta.get(IMAGE_METADATA_KEYS["md_file"], "")
                img_id = meta.get(IMAGE_METADATA_KEYS["image_id"], "")

                if src and src != expected_source:
                    issues.append(
                        {
                            "severity": "warning",
                            "file": rel,
                            "message": f"Image {img_ref}: source_file mismatch.",
                        }
                    )
                if md and md != md_path.name:
                    issues.append(
                        {
                            "severity": "warning",
                            "file": rel,
                            "message": f"Image {img_ref}: md_file mismatch.",
                        }
                    )
                # image_id should match alt text when using our format
                if img_id and alt_text.startswith(_IMAGE_ID_ALT_PREFIX):
                    expected_id = alt_text[len(_IMAGE_ID_ALT_PREFIX) :].strip()
                    if expected_id and img_id != expected_id:
                        issues.append(
                            {
                                "severity": "warning",
                                "file": rel,
                                "message": f"Image {img_ref}: image_id/alt mismatch.",
                            }
                        )

    return issues


def validate_single_file(md_path: Path, *, strict: bool = False) -> list[ValidationIssue]:
    """Validate one ``.md`` file (Markdown + images).

    Combines validate_markdown and validate_images. Checks:
    * File is non-empty and valid UTF-8.
    * Content parses as valid Markdown.
    * (strict) Every ``![alt](path)`` image reference resolves to an existing file.
    * Images are valid and metadata (if present) ties back to markdown.

    Args:
        md_path: Path to the Markdown file.
        strict: When True, broken image references are errors.

    Returns:
        List of ValidationIssue dicts; empty means the file is clean.
    """
    issues: list[ValidationIssue] = []
    issues.extend(validate_markdown(md_path))
    if issues and any(i["severity"] == "error" for i in issues):
        return issues  # Don't check images if we couldn't read markdown
    issues.extend(validate_images(md_path, strict=strict, check_metadata=True))
    return issues


def validate_output_tree(
    output_root: Path,
    *,
    strict: bool = False,
) -> list[ValidationIssue]:
    """Walk *output_root* and validate every ``.md`` file found.

    Args:
        output_root: Root directory (e.g. ``./transformed``).
        strict: Passed through to validate_single_file.

    Returns:
        All issues found across all files, sorted by file path.
    """
    all_issues: list[ValidationIssue] = []

    md_files = sorted(output_root.rglob("*.md"))
    if not md_files:
        all_issues.append(
            {
                "severity": "warning",
                "file": str(output_root),
                "message": "No .md files found in output directory.",
            }
        )
        return all_issues

    for md_path in md_files:
        all_issues.extend(validate_single_file(md_path, strict=strict))

    return all_issues
