"""Tests for pdf_markdown.discovery."""

from __future__ import annotations

from pathlib import Path

import pytest

from pdf_markdown.discovery import (
    collect_pdfs_from_folder,
    collect_pdfs_from_groups,
    collect_pdfs_from_inputs,
)

# ── Helpers ──────────────────────────────────────────────────────────────────


def _make_pdf_tree(root: Path, layout: dict[str, list[str]]) -> None:
    """Create folder/file tree from a mapping of group → list of filenames."""
    for group, names in layout.items():
        group_dir = root / group
        group_dir.mkdir(parents=True)
        for name in names:
            (group_dir / name).write_bytes(b"%PDF-1.4\n%%EOF\n")


# ── collect_pdfs_from_folder ─────────────────────────────────────────────────


def test_collect_from_folder_basic(tmp_path: Path) -> None:
    _make_pdf_tree(tmp_path, {"1880": ["a.pdf", "b.pdf"], "1890": ["c.pdf"]})

    results = collect_pdfs_from_folder(tmp_path)
    groups = [g for g, _ in results]
    names = [p.name for _, p in results]

    assert groups == ["1880", "1880", "1890"]
    assert names == ["a.pdf", "b.pdf", "c.pdf"]


def test_collect_from_folder_empty(tmp_path: Path) -> None:
    assert collect_pdfs_from_folder(tmp_path) == []


def test_collect_from_folder_ignores_non_pdf(tmp_path: Path) -> None:
    group_dir = tmp_path / "1880"
    group_dir.mkdir()
    (group_dir / "notes.txt").write_text("hello")
    (group_dir / "report.pdf").write_bytes(b"%PDF-1.4\n%%EOF\n")

    results = collect_pdfs_from_folder(tmp_path)
    assert len(results) == 1
    assert results[0][1].name == "report.pdf"


# ── collect_pdfs_from_groups ─────────────────────────────────────────────────


def test_collect_from_groups_subset(tmp_path: Path) -> None:
    _make_pdf_tree(tmp_path, {"1880": ["x.pdf"], "1890": ["y.pdf"], "1900": ["z.pdf"]})

    results = collect_pdfs_from_groups(tmp_path, ["1880", "1900"])
    assert [g for g, _ in results] == ["1880", "1900"]


def test_collect_from_groups_missing_raises(tmp_path: Path) -> None:
    _make_pdf_tree(tmp_path, {"1880": ["a.pdf"]})

    with pytest.raises(FileNotFoundError, match="1999"):
        collect_pdfs_from_groups(tmp_path, ["1880", "1999"])


# ── collect_pdfs_from_inputs ─────────────────────────────────────────────────


def test_collect_from_inputs_file(tmp_path: Path, tmp_pdf: Path) -> None:
    results = collect_pdfs_from_inputs([tmp_pdf])

    assert len(results) == 1
    group, path = results[0]
    assert path == tmp_pdf
    assert group == tmp_path.name


def test_collect_from_inputs_directory(tmp_path: Path) -> None:
    sub = tmp_path / "docs"
    sub.mkdir()
    (sub / "a.pdf").write_bytes(b"%PDF\n%%EOF\n")
    (sub / "b.pdf").write_bytes(b"%PDF\n%%EOF\n")

    results = collect_pdfs_from_inputs([sub])
    assert len(results) == 2
    assert all(g == "docs" for g, _ in results)


def test_collect_from_inputs_missing_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        collect_pdfs_from_inputs([tmp_path / "no_such.pdf"])


def test_collect_from_inputs_non_pdf_raises(tmp_path: Path) -> None:
    txt = tmp_path / "notes.txt"
    txt.write_text("hello")
    with pytest.raises(ValueError, match="not a PDF"):
        collect_pdfs_from_inputs([txt])


def test_collect_from_inputs_deduplicates(tmp_pdf: Path) -> None:
    results = collect_pdfs_from_inputs([tmp_pdf, tmp_pdf])
    assert len(results) == 1
