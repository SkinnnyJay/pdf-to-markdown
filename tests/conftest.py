"""Shared test fixtures."""

from pathlib import Path

import pytest


@pytest.fixture()
def tmp_pdf(tmp_path: Path) -> Path:
    """Return a path to a minimal (but structurally valid) single-page PDF."""
    pdf_bytes = (
        b"%PDF-1.4\n"
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\n"
        b"xref\n0 4\n0000000000 65535 f \n"
        b"0000000009 00000 n \n"
        b"0000000058 00000 n \n"
        b"0000000115 00000 n \n"
        b"trailer\n<< /Root 1 0 R /Size 4 >>\nstartxref\n190\n%%EOF\n"
    )
    p = tmp_path / "sample.pdf"
    p.write_bytes(pdf_bytes)
    return p
