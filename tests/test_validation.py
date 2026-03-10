"""Tests for pdf_markdown.validation."""

from pathlib import Path

from pdf_markdown.validation import (
    validate_images,
    validate_markdown,
    validate_output_tree,
    validate_pdf,
    validate_single_file,
)


def test_valid_file_no_issues(tmp_path: Path) -> None:
    md = tmp_path / "doc.md"
    md.write_text("# Hello\n\nSome content.\n", encoding="utf-8")
    assert validate_single_file(md) == []


def test_empty_file_is_error(tmp_path: Path) -> None:
    md = tmp_path / "empty.md"
    md.write_text("   \n", encoding="utf-8")
    issues = validate_single_file(md)
    assert any(i["severity"] == "error" and "empty" in i["message"].lower() for i in issues)


def test_image_ref_exists_no_issue(tmp_path: Path) -> None:
    # Create minimal valid PNG via Pillow (required for image format validation)
    from PIL import Image

    img = tmp_path / "img.png"
    Image.new("RGB", (1, 1), color="white").save(img)
    md = tmp_path / "doc.md"
    md.write_text("![alt](img.png)\n", encoding="utf-8")
    issues = validate_single_file(md, strict=True)
    assert issues == []


def test_missing_image_ref_warning_by_default(tmp_path: Path) -> None:
    md = tmp_path / "doc.md"
    md.write_text("![alt](missing.png)\n", encoding="utf-8")
    issues = validate_single_file(md, strict=False)
    assert len(issues) == 1
    assert issues[0]["severity"] == "warning"
    assert "missing.png" in issues[0]["message"]


def test_missing_image_ref_error_in_strict(tmp_path: Path) -> None:
    md = tmp_path / "doc.md"
    md.write_text("![alt](missing.png)\n", encoding="utf-8")
    issues = validate_single_file(md, strict=True)
    assert issues[0]["severity"] == "error"


def test_http_image_ref_skipped(tmp_path: Path) -> None:
    md = tmp_path / "doc.md"
    md.write_text("![alt](https://example.com/img.png)\n", encoding="utf-8")
    assert validate_single_file(md, strict=True) == []


def test_data_uri_skipped(tmp_path: Path) -> None:
    md = tmp_path / "doc.md"
    md.write_text("![alt](data:image/png;base64,abc123)\n", encoding="utf-8")
    assert validate_single_file(md, strict=True) == []


def test_validate_tree_all_valid(tmp_path: Path) -> None:
    (tmp_path / "1880").mkdir()
    (tmp_path / "1880" / "report.md").write_text("# Report\n\nContent.", encoding="utf-8")
    issues = validate_output_tree(tmp_path)
    assert issues == []


def test_validate_tree_empty_directory(tmp_path: Path) -> None:
    issues = validate_output_tree(tmp_path)
    assert len(issues) == 1
    assert issues[0]["severity"] == "warning"
    assert "No .md files" in issues[0]["message"]


def test_validate_tree_mixed_results(tmp_path: Path) -> None:
    good_dir = tmp_path / "1880"
    good_dir.mkdir()
    (good_dir / "good.md").write_text("# Good\n\nContent.", encoding="utf-8")

    bad_dir = tmp_path / "1890"
    bad_dir.mkdir()
    (bad_dir / "bad.md").write_text("   ", encoding="utf-8")

    issues = validate_output_tree(tmp_path)
    assert any(i["severity"] == "error" for i in issues)
    # The good file should not produce issues
    assert not any("good.md" in i["file"] for i in issues)


def test_validate_tree_strict_propagates(tmp_path: Path) -> None:
    d = tmp_path / "docs"
    d.mkdir()
    (d / "file.md").write_text("![x](ghost.png)\n", encoding="utf-8")

    non_strict = validate_output_tree(tmp_path, strict=False)
    strict = validate_output_tree(tmp_path, strict=True)

    assert non_strict[0]["severity"] == "warning"
    assert strict[0]["severity"] == "error"


def test_validate_pdf_valid(tmp_pdf: Path) -> None:
    assert validate_pdf(tmp_pdf) == []


def test_validate_pdf_missing(tmp_path: Path) -> None:
    issues = validate_pdf(tmp_path / "nonexistent.pdf")
    assert len(issues) == 1
    assert "does not exist" in issues[0]["message"]


def test_validate_markdown_valid(tmp_path: Path) -> None:
    md = tmp_path / "doc.md"
    md.write_text("# Hello\n\nContent.", encoding="utf-8")
    assert validate_markdown(md_path=md) == []


def test_validate_markdown_content_param() -> None:
    assert validate_markdown(content="# Hi") == []


def test_validate_images_missing_ref(tmp_path: Path) -> None:
    md = tmp_path / "doc.md"
    md.write_text("![x](missing.png)\n", encoding="utf-8")
    issues = validate_images(md, strict=False)
    assert len(issues) == 1
    assert "Missing" in issues[0]["message"]
