"""Marker invocation wrapper — convert a single PDF to Markdown via the marker CLI."""

from __future__ import annotations

import subprocess
from pathlib import Path

from pdf_markdown.models import ConversionResult

__all__ = ["ConversionResult", "find_marker_output", "run_marker"]


def run_marker(
    pdf: Path,
    output_dir: Path,
    *,
    batch_multiplier: int = 2,
    langs: str | None = None,
    timeout: int = 600,
) -> tuple[bool, str, str]:
    """Run ``marker_single`` on *pdf* and write markdown to *output_dir*.

    Args:
        pdf: Path to the source PDF.
        output_dir: Directory where Marker should write its output.
        batch_multiplier: Marker batch multiplier (controls GPU/CPU usage).
        langs: Comma-separated language hints passed to Marker (e.g. ``"English"``).
        timeout: Maximum seconds to wait for the subprocess.

    Returns:
        ``(success, stdout, stderr)`` tuple.
    """
    cmd: list[str] = [
        "marker_single",
        str(pdf),
        str(output_dir),
        "--batch_multiplier",
        str(batch_multiplier),
    ]
    if langs:
        cmd += ["--langs", langs]

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return proc.returncode == 0, proc.stdout, proc.stderr
    except FileNotFoundError:
        return (
            False,
            "",
            "marker_single not found. Install with: pip install marker-pdf",
        )
    except subprocess.TimeoutExpired:
        return False, "", f"Marker timed out after {timeout}s for {pdf.name}"


def find_marker_output(output_dir: Path, stem: str) -> Path | None:
    """Locate the markdown file Marker wrote for *stem* inside *output_dir*.

    Marker writes ``<output_dir>/<stem>/<stem>.md`` by default.

    Args:
        output_dir: Directory passed to Marker.
        stem: PDF filename without extension.

    Returns:
        Path to the ``.md`` file if it exists, otherwise ``None``.
    """
    candidate = output_dir / stem / f"{stem}.md"
    if candidate.exists():
        return candidate

    # Fallback: return the first .md found anywhere in the output tree.
    return next(output_dir.rglob("*.md"), None)
