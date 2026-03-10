"""Extract metadata from PDF files via PyMuPDF."""

from pathlib import Path

try:
    import fitz  # pymupdf
except ImportError:
    fitz = None  # type: ignore[assignment]

__all__ = ["get_pdf_metadata"]


def get_pdf_metadata(pdf: Path) -> dict[str, str]:
    """Extract metadata from a PDF file.

    Always includes ``source_file`` (the PDF basename). When PyMuPDF is
    available, also includes standard PDF metadata fields: author, title,
    subject, creator, producer, creationDate, modDate, keywords, format.

    Args:
        pdf: Path to the PDF file.

    Returns:
        Dict of string key-value pairs. Empty or missing PDF fields are
        omitted. On read errors, returns at least ``source_file``.
    """
    result: dict[str, str] = {"source_file": pdf.name}

    if fitz is None:
        return result

    try:
        doc = fitz.open(str(pdf))
        raw = doc.metadata
        doc.close()

        # PyMuPDF returns keys like "author", "title", etc.
        for key, value in raw.items():
            if value and isinstance(value, str):
                result[key] = value
    except Exception:
        pass

    return result
