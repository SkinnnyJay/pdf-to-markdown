"""Run logger — write structured per-run logs to the data directory."""

import json
from datetime import UTC, datetime
from pathlib import Path

from pdf_markdown.models import ConversionResult, RunSummary

__all__ = ["make_run_name", "read_run_log", "write_run_log"]

_LOG_VERSION = "1"


def write_run_log(summary: RunSummary, log_path: Path) -> None:
    """Serialise *summary* to a structured JSON-lines log file.

    Format is newline-delimited JSON (NDJSON): line 1 is the run header;
    subsequent lines are one object per :class:`~pdf_markdown.models.ConversionResult`.

    Args:
        summary: The completed :class:`RunSummary` to persist.
        log_path: Destination file path (parent directories are created).
    """
    log_path.parent.mkdir(parents=True, exist_ok=True)

    with log_path.open("w", encoding="utf-8") as fh:
        header = {
            "_type": "run_header",
            "_version": _LOG_VERSION,
            "run_name": summary.run_name,
            "started_at": summary.started_at.isoformat(),
            "finished_at": summary.finished_at.isoformat() if summary.finished_at else None,
            "total": summary.total,
            "ok": summary.ok_count,
            "fallback": summary.fallback_count,
            "failed": summary.failed_count,
            "success_rate": round(summary.success_rate, 2),
            "duration_s": summary.duration_s,
        }
        fh.write(json.dumps(header) + "\n")

        for r in summary.results:
            entry = {
                "_type": "result",
                "group": r.group,
                "pdf": str(r.pdf),
                "success": r.success,
                "is_fallback": r.is_fallback,
                "output_md": str(r.output_md) if r.output_md else None,
                "error": r.error,
                "stdout": r.stdout,
                "stderr": r.stderr,
                "duration_s": r.duration_s,
                "extracted_images": [str(p) for p in r.extracted_images],
                "worker_id": r.worker_id,
            }
            fh.write(json.dumps(entry) + "\n")


def read_run_log(log_path: Path) -> RunSummary:
    """Deserialise a log file written by :func:`write_run_log` into a :class:`RunSummary`.

    Args:
        log_path: Path to the NDJSON log file.

    Returns:
        Populated :class:`RunSummary` instance.

    Raises:
        FileNotFoundError: If *log_path* does not exist.
        ValueError: If the file format is unrecognised or corrupted.
    """
    if not log_path.exists():
        raise FileNotFoundError(f"Log file not found: {log_path}")

    lines = [ln for ln in log_path.read_text(encoding="utf-8").splitlines() if ln.strip()]
    if not lines:
        raise ValueError(f"Log file is empty: {log_path}")

    header = json.loads(lines[0])
    if header.get("_type") != "run_header":
        raise ValueError(f"First line is not a run_header: {log_path}")

    started_at = datetime.fromisoformat(header["started_at"])
    finished_at = (
        datetime.fromisoformat(header["finished_at"]) if header.get("finished_at") else None
    )

    results: list[ConversionResult] = []
    for line in lines[1:]:
        entry = json.loads(line)
        if entry.get("_type") != "result":
            continue
        results.append(
            ConversionResult(
                pdf=Path(entry["pdf"]),
                group=entry["group"],
                success=entry["success"],
                is_fallback=entry.get("is_fallback", False),
                output_md=Path(entry["output_md"]) if entry.get("output_md") else None,
                error=entry.get("error", ""),
                stdout=entry.get("stdout", ""),
                stderr=entry.get("stderr", ""),
                duration_s=entry.get("duration_s"),
                extracted_images=[Path(p) for p in entry.get("extracted_images", [])],
                worker_id=entry.get("worker_id"),
            )
        )

    return RunSummary(
        run_name=header["run_name"],
        started_at=started_at,
        finished_at=finished_at,
        results=results,
        log_path=log_path,
    )


def make_run_name(prefix: str = "") -> str:
    """Generate a sortable, URL-safe run name based on the current UTC time.

    Args:
        prefix: Optional string prepended before the timestamp.

    Returns:
        String like ``"convert-2026-03-09T14-05-32"`` or ``"2026-03-09T14-05-32"``.
    """
    ts = datetime.now(tz=UTC).strftime("%Y-%m-%dT%H-%M-%S")
    return f"{prefix}-{ts}" if prefix else ts
