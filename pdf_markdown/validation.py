"""Output validation — verify converted Markdown files and their assets.

Re-exports from pdf_markdown_validation for backward compatibility.
"""

from pdf_markdown.pdf_markdown_validation import (
    IMAGE_METADATA_KEYS,
    ValidationIssue,
    validate_images,
    validate_markdown,
    validate_output_tree,
    validate_pdf,
    validate_single_file,
)

__all__ = [
    "IMAGE_METADATA_KEYS",
    "ValidationIssue",
    "validate_images",
    "validate_markdown",
    "validate_output_tree",
    "validate_pdf",
    "validate_single_file",
]
