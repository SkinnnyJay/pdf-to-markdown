"""Output validation — verify converted Markdown files and their assets."""

import re
from pathlib import Path
from typing import Literal, TypedDict

__all__ = ["ValidationIssue", "validate_output_tree", "validate_single_file"]

_IMAGE_REF_RE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")


class ValidationIssue(TypedDict):
    """A single validation finding."""

    severity: Literal["error", "warning"]
    file: str
    message: str


def validate_single_file(md_path: Path, *, strict: bool = False) -> list[ValidationIssue]:
    """Validate one ``.md`` file.

    Checks performed:
    * File is non-empty.
    * File is valid UTF-8.
    * (strict) Every ``![alt](path)`` image reference resolves to an existing file.

    Args:
        md_path: Path to the Markdown file.
        strict: When ``True``, broken image references are reported as errors.

    Returns:
        List of :class:`ValidationIssue` dicts; empty means the file is clean.
    """
    issues: list[ValidationIssue] = []
    rel = str(md_path)

    try:
        content = md_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        issues.append({"severity": "error", "file": rel, "message": "File is not valid UTF-8."})
        return issues

    if not content.strip():
        issues.append({"severity": "error", "file": rel, "message": "File is empty."})
        return issues

    for match in _IMAGE_REF_RE.finditer(content):
        img_ref = match.group(1)
        if img_ref.startswith(("http://", "https://", "data:")):
            continue
        img_path = md_path.parent / img_ref
        if not img_path.exists():
            severity: Literal["error", "warning"] = "error" if strict else "warning"
            issues.append(
                {
                    "severity": severity,
                    "file": rel,
                    "message": f"Missing image reference: {img_ref}",
                }
            )

    return issues


def validate_output_tree(
    output_root: Path,
    *,
    strict: bool = False,
) -> list[ValidationIssue]:
    """Walk *output_root* and validate every ``.md`` file found.

    Args:
        output_root: Root directory (e.g. ``./transformed``).
        strict: Passed through to :func:`validate_single_file`.

    Returns:
        All issues found across all files, sorted by file path.
    """
    all_issues: list[ValidationIssue] = []

    md_files = sorted(output_root.rglob("*.md"))
    if not md_files:
        all_issues.append(
            {
                "severity": "warning",
                "file": str(output_root),
                "message": "No .md files found in output directory.",
            }
        )
        return all_issues

    for md_path in md_files:
        all_issues.extend(validate_single_file(md_path, strict=strict))

    return all_issues
