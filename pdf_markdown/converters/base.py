"""Converter protocol and result type."""

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass
class ConverterResult:
    """Result of a PDF-to-Markdown conversion attempt."""

    success: bool
    markdown: str
    images_dir: Path | None = None
    stdout: str = ""
    stderr: str = ""
    error: str = ""

    @property
    def has_images(self) -> bool:
        return self.images_dir is not None and self.images_dir.is_dir()


class Converter(Protocol):
    """Protocol for PDF-to-Markdown converter backends."""

    name: str
    description: str
    lightweight: bool

    def convert(
        self,
        pdf: Path,
        output_dir: Path,
        *,
        timeout: int = 600,
        **kwargs: object,
    ) -> ConverterResult:
        """Convert a PDF to Markdown.

        Args:
            pdf: Path to the source PDF.
            output_dir: Directory where the converter may write output (e.g. .md, images).
            timeout: Maximum seconds to wait (for subprocess-based converters).
            **kwargs: Backend-specific options.

        Returns:
            ConverterResult with success, markdown content, and optional images_dir.
        """
        ...
