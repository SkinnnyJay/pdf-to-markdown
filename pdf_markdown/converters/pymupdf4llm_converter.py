"""PyMuPDF4LLM converter — lightweight, no ML dependencies."""

from pathlib import Path


class PyMuPDF4LLMConverter:
    """Converter using pymupdf4llm (lightweight, PyMuPDF-based)."""

    name = "pymupdf4llm"
    description = "PyMuPDF4LLM — lightweight, no ML (good for native-text PDFs)"
    lightweight = True

    def convert(
        self,
        pdf: Path,
        output_dir: Path,
        *,
        timeout: int = 600,
        write_images: bool = True,
        **kwargs: object,
    ):
        from pdf_markdown.converters.base import ConverterResult

        try:
            import pymupdf4llm
        except ImportError:
            return ConverterResult(
                success=False,
                markdown="",
                error="pymupdf4llm not installed. Install with: pip install pymupdf4llm",
            )

        output_dir.mkdir(parents=True, exist_ok=True)
        img_path = str(output_dir) if write_images else ""

        try:
            md_text = pymupdf4llm.to_markdown(
                str(pdf),
                write_images=write_images,
                image_path=img_path,
            )
        except Exception as exc:
            return ConverterResult(
                success=False,
                markdown="",
                error=str(exc),
            )

        images_dir = None
        if write_images:
            imgs = list(output_dir.glob("*.png")) + list(output_dir.glob("*.jpg"))
            if imgs:
                images_dir = output_dir

        return ConverterResult(
            success=True,
            markdown=md_text if isinstance(md_text, str) else "",
            images_dir=images_dir,
        )
