"""Tests for pdf_markdown.run_logger."""

from datetime import UTC, datetime
from pathlib import Path

import pytest

from pdf_markdown.models import ConversionResult, RunSummary
from pdf_markdown.run_logger import make_run_name, read_run_log, write_run_log


def _make_summary(tmp_path: Path) -> RunSummary:
    results = [
        ConversionResult(
            pdf=Path("/src/1880/report.pdf"),
            group="1880",
            success=True,
            output_md=tmp_path / "1880" / "report.md",
            stdout="ok",
            stderr="",
            duration_s=3.2,
        ),
        ConversionResult(
            pdf=Path("/src/1890/broken.pdf"),
            group="1890",
            success=False,
            is_fallback=True,
            output_md=tmp_path / "1890" / "broken.md",
            error="Marker crashed",
            stderr="something went wrong",
            extracted_images=[Path("/out/1890/broken_assets/broken-p001.png")],
            duration_s=12.5,
        ),
    ]
    return RunSummary(
        run_name="test-run",
        started_at=datetime(2026, 3, 9, 12, 0, 0, tzinfo=UTC),
        finished_at=datetime(2026, 3, 9, 12, 0, 16, tzinfo=UTC),
        results=results,
        log_path=tmp_path / "output.log",
    )


def test_round_trip(tmp_path: Path) -> None:
    summary = _make_summary(tmp_path)
    log_path = tmp_path / "output.log"

    write_run_log(summary, log_path)
    assert log_path.exists()

    loaded = read_run_log(log_path)
    assert loaded.run_name == "test-run"
    assert len(loaded.results) == 2

    r0 = loaded.results[0]
    assert r0.success is True
    assert r0.group == "1880"
    assert r0.duration_s == pytest.approx(3.2)

    r1 = loaded.results[1]
    assert r1.success is False
    assert r1.is_fallback is True
    assert r1.error == "Marker crashed"
    assert len(r1.extracted_images) == 1


def test_write_creates_parent_dirs(tmp_path: Path) -> None:
    summary = _make_summary(tmp_path)
    deep = tmp_path / "a" / "b" / "c" / "output.log"
    write_run_log(summary, deep)
    assert deep.exists()


def test_read_missing_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        read_run_log(tmp_path / "nope.log")


def test_read_empty_raises(tmp_path: Path) -> None:
    log = tmp_path / "output.log"
    log.write_text("", encoding="utf-8")
    with pytest.raises(ValueError, match="empty"):
        read_run_log(log)


def test_read_bad_header_raises(tmp_path: Path) -> None:
    log = tmp_path / "output.log"
    log.write_text('{"_type": "something_else"}\n', encoding="utf-8")
    with pytest.raises(ValueError, match="run_header"):
        read_run_log(log)


def test_make_run_name_format() -> None:
    name = make_run_name("convert")
    assert name.startswith("convert-")
    assert len(name) > 10


def test_make_run_name_no_prefix() -> None:
    name = make_run_name()
    assert name[4] == "-" and name[7] == "-"  # YYYY-MM-DD…


def test_metrics(tmp_path: Path) -> None:
    summary = _make_summary(tmp_path)
    assert summary.total == 2
    assert summary.ok_count == 1
    assert summary.fallback_count == 1
    assert summary.failed_count == 0
    assert summary.success_rate == pytest.approx(50.0)
    assert summary.duration_s == pytest.approx(16.0)


def test_worker_id_round_trip(tmp_path: Path) -> None:
    """worker_id is persisted and restored from log."""
    result = ConversionResult(
        pdf=Path("/src/1880/doc.pdf"),
        group="1880",
        success=True,
        output_md=tmp_path / "1880" / "doc.md",
        worker_id=2,
    )
    summary = RunSummary(
        run_name="parallel-run",
        started_at=datetime(2026, 3, 9, 12, 0, 0, tzinfo=UTC),
        finished_at=datetime(2026, 3, 9, 12, 0, 5, tzinfo=UTC),
        results=[result],
        log_path=tmp_path / "output.log",
    )
    write_run_log(summary, summary.log_path)
    loaded = read_run_log(summary.log_path)
    assert loaded.results[0].worker_id == 2
