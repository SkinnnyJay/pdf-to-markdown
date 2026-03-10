"""Runtime configuration loaded from environment / .env file.

All settings have sensible defaults and can be overridden by placing a
``.env`` file in the working directory or by setting environment variables
directly.

Example ``.env``::

    PDF_MARKDOWN_DATA_DIR=./data
    PDF_MARKDOWN_LOG_SUBDIR=runs
    PDF_MARKDOWN_REPORT_TITLE=PDF Conversion Report
    PDF_MARKDOWN_OPEN_REPORT=true
    PDF_MARKDOWN_WORKERS=1
    PDF_MARKDOWN_MODEL_PATH=/path/to/hf-cache
"""

import os
from pathlib import Path

__all__ = ["Settings", "settings"]


def _env(key: str, default: str) -> str:
    return os.environ.get(key, default)


def _env_int(key: str, default: int) -> int:
    raw = os.environ.get(key)
    if raw is None:
        return default
    try:
        return max(1, int(raw))
    except ValueError:
        return default


def _load_dotenv(dotenv_path: Path) -> None:
    """Minimal .env loader — no external dependencies required."""
    if not dotenv_path.is_file():
        return
    for raw_line in dotenv_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key not in os.environ:
            os.environ[key] = value


class Settings:
    """Centralised runtime settings for pdf-markdown.

    Loaded once at import time from ``.env`` and the process environment.
    Instantiate with ``dotenv=`` to override the path (useful in tests).
    """

    def __init__(self, *, dotenv: Path | None = None) -> None:
        _load_dotenv(dotenv or Path(".env"))

        self.data_dir: Path = Path(_env("PDF_MARKDOWN_DATA_DIR", "./data"))
        self.log_subdir: str = _env("PDF_MARKDOWN_LOG_SUBDIR", "runs")
        self.report_title: str = _env("PDF_MARKDOWN_REPORT_TITLE", "PDF Conversion Report")
        self.open_report: bool = _env("PDF_MARKDOWN_OPEN_REPORT", "false").lower() in (
            "1",
            "true",
            "yes",
        )
        self.workers: int = _env_int("PDF_MARKDOWN_WORKERS", 1)
        _mp = _env("PDF_MARKDOWN_MODEL_PATH", "").strip()
        self.model_path: Path | None = Path(_mp) if _mp else None
        self.converter: str = _env("PDF_MARKDOWN_CONVERTER", "marker").strip().lower()

    def run_dir(self, run_name: str) -> Path:
        """``<data_dir>/<log_subdir>/<run_name>/`` — not yet created."""
        return self.data_dir / self.log_subdir / run_name

    def log_path(self, run_name: str) -> Path:
        """``<run_dir>/output.log``"""
        return self.run_dir(run_name) / "output.log"

    def report_path(self, run_name: str) -> Path:
        """``<run_dir>/report.html``"""
        return self.run_dir(run_name) / "report.html"


# Module-level singleton — re-read on each import so tests can patch env vars.
settings = Settings()
