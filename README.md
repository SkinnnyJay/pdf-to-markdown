# pdf-markdown

> Convert PDF files to Markdown using [Marker](https://github.com/datalab-to/marker), with automatic image-extraction fallback when conversion fails.

`pdf-markdown` is a reusable, installable Python CLI that handles any folder of PDFs — not just a single use-case. It is designed to be picked up by anyone and pointed at any collection of PDFs.

---

## Features

- **Marker-powered** — leverages `marker_single` for high-quality, layout-aware Markdown output.
- **Fallback extraction** — if Marker fails, pages are rasterised to PNG via `pymupdf` and a placeholder Markdown file is generated that embeds every extracted image.
- **Generic group model** — works with any folder tree `<source>/<group>/*.pdf` (years, topics, departments — anything).
- **Rich terminal UI** — colourised progress bar and summary table via [Rich](https://github.com/Textualize/rich).
- **Typer CLI** — full `--help`, shell completion, typed options.
- **Makefile** — one-liner commands for install, format, lint, test, and batch conversion.

---

## Requirements

| Requirement | Minimum version |
|---|---|
| Python | 3.11 |
| [Marker](https://github.com/datalab-to/marker) | 0.3.x (`marker_single` in PATH) |
| pymupdf | 1.24 (fallback image extraction) |

---

## Installation

```bash
# 1. Clone or copy this folder
cd pdf-markdown

# 2. Create a virtual environment and install (Makefile shortcut)
make install-dev

# — or manually —
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

After installation the `pdf-markdown` command is available in your virtual environment.

---

## Quick Start

### Convert a folder tree organised by group

```
archive/
  1880/
    census_1880.pdf
    report_A.pdf
  1890/
    census_1890.pdf
```

```bash
pdf-markdown convert --source ./archive --output ./transformed
```

Output:

```
transformed/
  1880/
    census_1880.md
    report_A.md
  1890/
    census_1890.md
```

### Convert only specific groups

```bash
pdf-markdown convert --source ./archive --groups 1880,1900 --output ./transformed
```

### Convert explicit files or folders

```bash
# Single file
pdf-markdown convert --input ./archive/1880/census.pdf --output ./transformed

# Whole folder
pdf-markdown convert --input ./archive/1880 --output ./transformed

# Mix of files and folders
pdf-markdown convert \
  --input ./archive/1880/report.pdf \
  --input ./archive/1890 \
  --output ./transformed
```

### Preview without writing (dry run)

```bash
pdf-markdown convert --source ./archive --dry-run
```

---

## CLI Reference

```
pdf-markdown convert [OPTIONS]
```

| Option | Default | Description |
|---|---|---|
| `--source`, `-s` | — | Root folder with `<group>/` sub-folders |
| `--groups`, `-g` | all groups | Comma-separated group names to process (requires `--source`) |
| `--input`, `-i` | — | Explicit PDF file or folder (repeatable) |
| `--output`, `-o` | `transformed` | Root output directory |
| `--batch-multiplier` | `2` | Marker batch multiplier (higher = more RAM) |
| `--langs` | — | Comma-separated language hints for Marker, e.g. `English,German` |
| `--timeout` | `600` | Per-file Marker timeout in seconds |
| `--dry-run` | `false` | Show what would be processed, then exit |
| `--version`, `-V` | — | Print version and exit |

---

## Fallback Behaviour

When `marker_single` is unavailable or exits non-zero:

1. Each page of the PDF is rasterised to a PNG at 150 dpi into `<output>/<group>/<stem>_assets/`.
2. A placeholder `<output>/<group>/<stem>.md` is created:

```markdown
# census_1880

> **Note:** Automatic Markdown conversion failed for this file.
> Reason: `Marker returned non-zero exit code.`
>
> Page images have been extracted and are embedded below.

---

![census_1880-p001.png](census_1880_assets/census_1880-p001.png)

![census_1880-p002.png](census_1880_assets/census_1880-p002.png)
```

Exit code is `1` when any file fails or falls back.

---

## Makefile Commands

```bash
make help          # Show all targets
make install       # Install runtime deps
make install-dev   # Install with dev/test deps
make format        # Auto-format code (ruff)
make lint          # Lint code (ruff)
make lint-fix      # Lint + auto-fix safe issues
make check         # Format then lint
make test          # Run tests
make test-cov      # Run tests with coverage report
make dry-run       # Preview SOURCE= folder (no writes)
make run           # Convert SOURCE= → OUTPUT=
make run-groups    # Convert specific GROUPS= in SOURCE=
make run-input     # Convert a single INPUT= file or folder
make clean         # Remove build artefacts
make clean-all     # Remove build artefacts + venv
```

Pass variables inline:

```bash
make run SOURCE=/Volumes/Krusty GROUPS=1880,1890,1900,1910 OUTPUT=/Volumes/Krusty/transformed
```

---

## Development

```bash
make install-dev   # install with dev deps
make check         # format + lint
make test          # run all tests
make test-cov      # tests with coverage
```

### Project layout

```
pdf-markdown/
├── src/
│   └── pdf_markdown/
│       ├── __init__.py        # package version
│       ├── cli.py             # Typer CLI entrypoint
│       ├── discovery.py       # PDF file resolution
│       ├── marker_runner.py   # Marker subprocess wrapper
│       ├── fallback_images.py # Image extraction & placeholder MD
│       └── output.py          # Output path helpers & file writing
├── tests/
│   ├── conftest.py
│   ├── test_cli.py
│   ├── test_discovery.py
│   ├── test_fallback.py
│   ├── test_marker_runner.py
│   └── test_output.py
├── pyproject.toml
├── Makefile
└── README.md
```

---

## License

MIT
