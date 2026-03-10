"""Marker (marker-pdf) converter — high-quality, layout-aware, ML-powered."""

from pathlib import Path

from pdf_markdown.marker_runner import find_marker_output, run_marker


class MarkerConverter:
    """Converter using marker_single CLI (marker-pdf)."""

    name = "marker"
    description = "Marker — high-quality layout-aware conversion (ML/PyTorch)"
    lightweight = False

    def convert(
        self,
        pdf: Path,
        output_dir: Path,
        *,
        timeout: int = 600,
        model_path: Path | None = None,
        **kwargs: object,
    ):
        from pdf_markdown.converters.base import ConverterResult

        success, stdout, stderr = run_marker(
            pdf,
            output_dir,
            timeout=timeout,
            model_path=model_path,
        )

        if not success:
            return ConverterResult(
                success=False,
                markdown="",
                stdout=stdout,
                stderr=stderr,
                error=stderr or "Marker returned non-zero exit code.",
            )

        md_path = find_marker_output(output_dir, pdf.stem)
        if not md_path:
            return ConverterResult(
                success=False,
                markdown="",
                stdout=stdout,
                stderr=stderr,
                error="Marker exited 0 but produced no .md output.",
            )

        markdown = md_path.read_text(encoding="utf-8")
        # Marker may write images to stem/images/ or directly in stem/ (v1.10+)
        images_dir = md_path.parent / "images"
        if not images_dir.is_dir():
            images_dir = None
        if images_dir is None:
            for p in md_path.parent.iterdir():
                if p.suffix.lower() in (".png", ".jpg", ".jpeg"):
                    images_dir = md_path.parent
                    break

        return ConverterResult(
            success=True,
            markdown=markdown,
            images_dir=images_dir,
            stdout=stdout,
            stderr=stderr,
        )
