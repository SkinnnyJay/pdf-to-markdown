"""Marker invocation wrapper — convert a single PDF to Markdown via the marker CLI."""

import os
import subprocess
from pathlib import Path

__all__ = ["find_marker_output", "run_marker"]


def run_marker(
    pdf: Path,
    output_dir: Path,
    *,
    batch_multiplier: int = 2,  # noqa: ARG001 — reserved for older marker versions
    langs: str | None = None,  # noqa: ARG001 — reserved for older marker versions
    timeout: int = 600,
    model_path: Path | None = None,
) -> tuple[bool, str, str]:
    """Run ``marker_single`` on *pdf* and write markdown to *output_dir*.

    Args:
        pdf: Path to the source PDF.
        output_dir: Directory where Marker should write its output.
        batch_multiplier: Unused — kept for API compatibility with older marker versions.
        langs: Unused — kept for API compatibility with older marker versions.
        timeout: Maximum seconds to wait for the subprocess.
        model_path: Optional path for HuggingFace model cache (sets HF_HOME in subprocess env).

    Returns:
        ``(success, stdout, stderr)`` tuple.
    """
    cmd: list[str] = [
        "marker_single",
        str(pdf),
        "--output_dir",
        str(output_dir),
    ]

    env = os.environ.copy()
    if model_path is not None:
        env["HF_HOME"] = str(model_path)

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            env=env,
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

    Marker writes ``<output_dir>/<stem>/<stem>.md`` by default; falls back to
    returning the first ``.md`` found anywhere in the tree.

    Args:
        output_dir: Directory passed to Marker.
        stem: PDF filename without extension.

    Returns:
        Path to the ``.md`` file if it exists, otherwise ``None``.
    """
    candidate = output_dir / stem / f"{stem}.md"
    if candidate.exists():
        return candidate
    return next(output_dir.rglob("*.md"), None)
