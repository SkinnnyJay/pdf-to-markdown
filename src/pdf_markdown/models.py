"""Domain models shared across pdf-markdown modules."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

__all__ = ["ConversionResult", "RunSummary"]


@dataclass
class ConversionResult:
    """Outcome of a single Marker conversion attempt.

    Attributes:
        pdf: Path to the source PDF file.
        group: Group name (sub-folder, e.g. ``"1880"``).
        success: ``True`` if Marker produced usable Markdown output.
        output_md: Path to the written ``.md`` file (present even on fallback).
        stdout: Captured stdout from the Marker subprocess.
        stderr: Captured stderr from the Marker subprocess.
        error: Human-readable error description when ``success`` is ``False``.
        extracted_images: Images extracted during fallback (empty on success).
        duration_s: Wall-clock seconds the conversion took (``None`` if unknown).
        is_fallback: ``True`` when the result came from the image-extraction fallback.
    """

    pdf: Path
    group: str
    success: bool
    output_md: Path | None = None
    stdout: str = ""
    stderr: str = ""
    error: str = ""
    extracted_images: list[Path] = field(default_factory=list)
    duration_s: float | None = None
    is_fallback: bool = False

    @property
    def status_label(self) -> str:
        """Human-readable one-word status for use in reports."""
        if self.success:
            return "ok"
        return "fallback" if self.is_fallback else "failed"

    @property
    def log_text(self) -> str:
        """Combine stdout + stderr into a single log blob."""
        parts = []
        if self.stdout.strip():
            parts.append(f"=== stdout ===\n{self.stdout.strip()}")
        if self.stderr.strip():
            parts.append(f"=== stderr ===\n{self.stderr.strip()}")
        if self.error.strip():
            parts.append(f"=== error ===\n{self.error.strip()}")
        return "\n\n".join(parts) if parts else "(no output captured)"


@dataclass
class RunSummary:
    """Metadata and aggregate statistics for a single conversion run.

    Attributes:
        run_name: Unique slug for this run (used in directory names).
        started_at: UTC timestamp when the run began.
        finished_at: UTC timestamp when the run ended (``None`` if still running).
        results: All :class:`ConversionResult` objects from this run.
        log_path: Path to the ``output.log`` file for this run.
        report_path: Path to the generated ``report.html`` (set after generation).
    """

    run_name: str
    started_at: datetime
    finished_at: datetime | None = None
    results: list[ConversionResult] = field(default_factory=list)
    log_path: Path | None = None
    report_path: Path | None = None

    # ── Derived metrics ───────────────────────────────────────────────────────

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def ok_count(self) -> int:
        return sum(1 for r in self.results if r.success)

    @property
    def fallback_count(self) -> int:
        return sum(1 for r in self.results if r.is_fallback and not r.success)

    @property
    def failed_count(self) -> int:
        return sum(1 for r in self.results if not r.success and not r.is_fallback)

    @property
    def success_rate(self) -> float:
        return (self.ok_count / self.total * 100) if self.total else 0.0

    @property
    def duration_s(self) -> float | None:
        if self.started_at and self.finished_at:
            return (self.finished_at - self.started_at).total_seconds()
        return None

    @property
    def groups(self) -> list[str]:
        """Unique group names in insertion order."""
        seen: set[str] = set()
        out: list[str] = []
        for r in self.results:
            if r.group not in seen:
                seen.add(r.group)
                out.append(r.group)
        return out
