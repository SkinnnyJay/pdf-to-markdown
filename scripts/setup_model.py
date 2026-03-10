#!/usr/bin/env python3
"""Pre-download Marker models for the current environment.

Runs marker_single on a minimal PDF to trigger model download. Respects
PDF_MARKDOWN_MODEL_PATH (HF_HOME) from .env or environment.

Usage:
    python scripts/setup_model.py
    make setup-model
"""

import os
import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from pdf_markdown.config import Settings  # noqa: E402


def _minimal_pdf() -> bytes:
    """Minimal valid single-page PDF."""
    return (
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


def main() -> int:
    cfg = Settings()
    model_path = cfg.model_path

    with subprocess.Popen(
        [sys.executable, "-c", "import tempfile; print(tempfile.gettempdir())"],
        capture_output=True,
        text=True,
    ) as proc:
        tmp_base = Path(proc.communicate()[0].strip())
    work_dir = tmp_base / "pdf-markdown-setup"
    work_dir.mkdir(exist_ok=True)

    pdf_path = work_dir / "setup_model.pdf"
    pdf_path.write_bytes(_minimal_pdf())

    out_dir = work_dir / "out"
    out_dir.mkdir(exist_ok=True)

    env = os.environ.copy()
    if model_path is not None:
        env["HF_HOME"] = str(model_path)
        print(f"Using model path: {model_path}", file=sys.stderr)
    else:
        print("Using default HuggingFace cache (~/.cache/huggingface)", file=sys.stderr)

    print("Downloading Marker models (first run may take several minutes)...", file=sys.stderr)
    try:
        proc = subprocess.run(
            ["marker_single", str(pdf_path), "--output_dir", str(out_dir)],
            env=env,
            capture_output=True,
            text=True,
            timeout=600,
        )
    except FileNotFoundError:
        print(
            "ERROR: marker_single not found. Install with: pip install marker-pdf",
            file=sys.stderr,
        )
        return 1
    except subprocess.TimeoutExpired:
        print("ERROR: Model download timed out after 10 minutes.", file=sys.stderr)
        return 1

    # Cleanup
    try:
        pdf_path.unlink(missing_ok=True)
        for p in out_dir.rglob("*"):
            p.unlink()
        out_dir.rmdir()
        work_dir.rmdir()
    except OSError:
        pass

    if proc.returncode != 0:
        print(f"WARNING: marker_single exited {proc.returncode}", file=sys.stderr)
        if proc.stderr:
            print(proc.stderr, file=sys.stderr)
        return 1

    print("Models ready.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
