"""Tests for pdf_markdown.config."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from pdf_markdown.config import Settings


def test_defaults() -> None:
    s = Settings(dotenv=Path("/nonexistent/.env"))
    assert s.data_dir == Path("./data")
    assert s.log_subdir == "runs"
    assert s.report_title == "PDF Conversion Report"
    assert s.open_report is False


def test_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PDF_MARKDOWN_DATA_DIR", "/tmp/mydata")
    monkeypatch.setenv("PDF_MARKDOWN_REPORT_TITLE", "My Report")
    monkeypatch.setenv("PDF_MARKDOWN_OPEN_REPORT", "true")
    s = Settings(dotenv=Path("/nonexistent/.env"))
    assert s.data_dir == Path("/tmp/mydata")
    assert s.report_title == "My Report"
    assert s.open_report is True


def test_dotenv_loading(tmp_path: Path) -> None:
    dotenv = tmp_path / ".env"
    dotenv.write_text('PDF_MARKDOWN_REPORT_TITLE="From dotenv"\n', encoding="utf-8")
    # Temporarily unset so dotenv can set it
    old = os.environ.pop("PDF_MARKDOWN_REPORT_TITLE", None)
    try:
        s = Settings(dotenv=dotenv)
        assert s.report_title == "From dotenv"
    finally:
        if old is not None:
            os.environ["PDF_MARKDOWN_REPORT_TITLE"] = old


def test_run_dir(tmp_path: Path) -> None:
    s = Settings(dotenv=Path("/nonexistent/.env"))
    s.data_dir = tmp_path
    rd = s.run_dir("my-run")
    assert rd == tmp_path / "runs" / "my-run"


def test_log_path(tmp_path: Path) -> None:
    s = Settings(dotenv=Path("/nonexistent/.env"))
    s.data_dir = tmp_path
    assert s.log_path("r1") == tmp_path / "runs" / "r1" / "output.log"


def test_report_path(tmp_path: Path) -> None:
    s = Settings(dotenv=Path("/nonexistent/.env"))
    s.data_dir = tmp_path
    assert s.report_path("r1") == tmp_path / "runs" / "r1" / "report.html"
