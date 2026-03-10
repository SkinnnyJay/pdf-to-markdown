#!/usr/bin/env python3
"""Standalone validation script for CI or manual inspection.

Usage:
    python scripts/validate_output.py ./transformed
    python scripts/validate_output.py ./transformed --strict
    python scripts/validate_output.py ./transformed --json > report.json

Exit codes:
    0  — all files are valid.
    1  — one or more errors (or warnings in strict mode).
    2  — bad arguments / output path does not exist.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Allow running directly without installing the package.
_ROOT = Path(__file__).parent.parent / "src"
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from pdf_markdown.validation import validate_output_tree  # noqa: E402


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="validate_output",
        description="Validate pdf-markdown converted output directory.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "output",
        type=Path,
        help="Root output directory to validate (e.g. ./transformed).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat missing image references as errors instead of warnings.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="Emit results as JSON to stdout (useful for CI reporting).",
    )
    return parser.parse_args()


def _colour(text: str, code: str) -> str:
    """ANSI colour wrap — skipped when stdout is not a TTY."""
    if not sys.stdout.isatty():
        return text
    return f"\033[{code}m{text}\033[0m"


def main() -> int:
    args = _parse_args()

    if not args.output.is_dir():
        print(
            f"Error: output path does not exist or is not a directory: {args.output}",
            file=sys.stderr,
        )
        return 2

    issues = validate_output_tree(args.output, strict=args.strict)

    if args.as_json:
        print(json.dumps(issues, indent=2))
        return 1 if issues else 0

    if not issues:
        print(_colour(f"✓ All files valid in {args.output}", "32"))
        return 0

    # Human-readable table
    errors = [i for i in issues if i["severity"] == "error"]
    warnings = [i for i in issues if i["severity"] == "warning"]

    col_w = max(len(i["file"]) for i in issues) + 2
    header = f"{'File':<{col_w}}  {'Severity':<9}  Issue"
    print(header)
    print("-" * len(header))

    for issue in issues:
        sev = issue["severity"]
        colour_code = "31" if sev == "error" else "33"
        print(f"{issue['file']:<{col_w}}  {_colour(sev, colour_code):<9}  {issue['message']}")

    print()
    if errors:
        print(_colour(f"✗ {len(errors)} error(s), {len(warnings)} warning(s).", "31"))
    else:
        print(_colour(f"⚠ {len(warnings)} warning(s) (no errors).", "33"))

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
