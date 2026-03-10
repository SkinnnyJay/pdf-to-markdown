#!/usr/bin/env python3
"""Generate valid Shakespeare PDFs for testing.

Output: <TEST_DATA_DIR>/shakespeare/Shakespeare-<Title>-<Year>.pdf

Uses TEST_DATA_DIR from .env or environment. Supports --count to limit
how many plays to generate.

Usage:
    python scripts/generate_shakespeare_pdfs.py [--count N]
    make generate-shakespeare [COUNT=N]
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

import fitz


# Minimal .env loader (no external deps)
def _load_dotenv(dotenv_path: Path) -> None:
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


# Shakespeare plays with approximate year (scholarly consensus)
SHAKESPEARE_PLAYS: list[tuple[str, int]] = [
    ("The Comedy of Errors", 1589),
    ("Henry VI Part III", 1590),
    ("Henry VI Part II", 1590),
    ("Henry VI Part I", 1591),
    ("Richard III", 1592),
    ("Titus Andronicus", 1593),
    ("The Taming of the Shrew", 1593),
    ("The Two Gentlemen of Verona", 1594),
    ("Romeo and Juliet", 1594),
    ("Love's Labour's Lost", 1594),
    ("A Midsummer Night's Dream", 1595),
    ("Richard II", 1595),
    ("King John", 1596),
    ("The Merchant of Venice", 1596),
    ("Henry IV Part I", 1597),
    ("Henry IV Part II", 1597),
    ("Much Ado About Nothing", 1598),
    ("Henry V", 1598),
    ("Julius Caesar", 1599),
    ("As You Like It", 1599),
    ("Twelfth Night", 1599),
    ("Hamlet", 1600),
    ("The Merry Wives of Windsor", 1600),
    ("Troilus and Cressida", 1601),
    ("All's Well That Ends Well", 1602),
    ("Othello", 1604),
    ("Measure for Measure", 1604),
    ("Macbeth", 1605),
    ("King Lear", 1605),
    ("Antony and Cleopatra", 1606),
    ("Timon of Athens", 1607),
    ("Coriolanus", 1607),
    ("Pericles", 1608),
    ("Cymbeline", 1609),
    ("The Winter's Tale", 1610),
    ("The Tempest", 1611),
    ("Henry VIII", 1612),
    ("The Two Noble Kinsmen", 1613),
]


def slugify(title: str) -> str:
    """Convert title to filename-safe slug: lowercase, hyphens, no special chars."""
    s = title.replace("'", "").replace("'", "").replace("'", "")
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s


def format_filename(title: str, year: int) -> str:
    """Format as: Shakespeare-Title-Year.pdf (name-title-year)."""
    slug = slugify(title)
    parts = [p.capitalize() for p in slug.split("-") if p]
    title_part = "-".join(parts)
    return f"Shakespeare-{title_part}-{year}.pdf"


def create_valid_pdf(output_path: Path, title: str, year: int) -> None:
    """Create a valid PDF with title, author, and sample content."""
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)

    doc.set_metadata(
        {
            "title": title,
            "author": "William Shakespeare",
            "subject": f"Play, {year}",
            "creator": "generate_shakespeare_pdfs.py",
        }
    )

    rect = fitz.Rect(50, 50, 545, 792)
    text = f"{title}\n\nWilliam Shakespeare\n\nFirst performed circa {year}\n\n"
    text += (
        "This is a placeholder PDF for testing PDF-to-Markdown conversion. "
        "The full text of this play is in the public domain and available "
        "from Project Gutenberg, Open Source Shakespeare, and other sources."
    )
    page.insert_textbox(rect, text, fontsize=12, fontname="helv")

    doc.save(str(output_path), garbage=4, deflate=True)
    doc.close()


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    _load_dotenv(repo_root / ".env")

    default_test_data = (repo_root / ".." / "testData").resolve()
    test_data_dir = Path(os.environ.get("TEST_DATA_DIR", str(default_test_data)))
    out_dir = test_data_dir / "shakespeare"

    parser = argparse.ArgumentParser(description="Generate valid Shakespeare PDFs for testing.")
    parser.add_argument(
        "--count",
        "-n",
        type=int,
        default=None,
        metavar="N",
        help=f"Number of plays to generate (default: all {len(SHAKESPEARE_PLAYS)})",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=out_dir,
        help="Output directory (default: TEST_DATA_DIR/shakespeare)",
    )
    args = parser.parse_args()

    plays = SHAKESPEARE_PLAYS
    if args.count is not None:
        if args.count < 1:
            print("Error: --count must be >= 1", file=sys.stderr)
            return 1
        plays = plays[: args.count]

    args.output.mkdir(parents=True, exist_ok=True)

    for title, year in plays:
        filename = format_filename(title, year)
        path = args.output / filename
        create_valid_pdf(path, title, year)
        print(f"Created: {path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
