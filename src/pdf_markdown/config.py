"""Runtime configuration loaded from environment / .env file.

All settings have sensible defaults and can be overridden by placing a
``.env`` file in the working directory or by setting environment variables
directly.

Example ``.env``::

    PDF_MARKDOWN_DATA_DIR=./data
    PDF_MARKDOWN_LOG_SUBDIR=runs
    PDF_MARKDOWN_REPORT_TITLE=PDF Conversion Report
    PDF_MARKDOWN_OPEN_REPORT=true
"""

from __future__ import annotations

import os
from pathlib import Path

__all__ = ["Settings", "settings"]


def _env(key: str, default: str) -> str:
    return os.environ.get(key, default)


def _load_dotenv(dotenv_path: Path) -> None:
    """Minimal .env loader — no external dependencies required."""
    if not dotenv_path.is_file():
        return
    for line in dotenv_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        # Only set if not already in the environment (env takes priority).
        if key not in os.environ:
            os.environ[key] = value


class Settings:
    """Centralised runtime settings for pdf-markdown.

    Attributes:
        data_dir: Root directory for all run data and logs.
        log_subdir: Sub-directory name written under ``data_dir/<run_title>/``.
        report_title: Default HTML report title.
        open_report: When ``True``, the CLI opens the report in the browser after generation.
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

    def run_dir(self, run_name: str) -> Path:
        """Return the directory for a named run's data.

        Layout: ``<data_dir>/<log_subdir>/<run_name>/``

        Args:
            run_name: Slug used to identify this conversion run
                      (e.g. ``"1880-2026-03-09"``).

        Returns:
            Path to the run directory (not yet created).
        """
        return self.data_dir / self.log_subdir / run_name

    def log_path(self, run_name: str) -> Path:
        """Return the canonical ``output.log`` path for a run.

        Args:
            run_name: Same slug passed to :meth:`run_dir`.

        Returns:
            Path to ``<run_dir>/output.log``.
        """
        return self.run_dir(run_name) / "output.log"

    def report_path(self, run_name: str) -> Path:
        """Return the canonical ``report.html`` path for a run.

        Args:
            run_name: Same slug passed to :meth:`run_dir`.

        Returns:
            Path to ``<run_dir>/report.html``.
        """
        return self.run_dir(run_name) / "report.html"


# Module-level singleton — re-read on each import so tests can patch env vars.
settings = Settings()
