<div align="center">
  <img src="banner.png" alt="PDF-to-Markdown" />
</div>

# pdf-markdown

> Convert PDFs to Markdown using [Marker](https://github.com/datalab-to/marker), with automatic image-extraction fallback when conversion fails.

`pdf-markdown` is an installable Python CLI that works with any folder of PDFs. Point it at a directory tree, get back clean Markdown — plus an interactive HTML report showing what succeeded, what fell back, and why.

---

## Features

- **Marker-powered** — uses `marker_single` for high-quality, layout-aware Markdown output.
- **Embedded metadata** — PDF metadata (source file, author, title, etc.) is stored in a hidden HTML comment at the top of each `.md` file, invisible when rendered but available when editing or via `extract_metadata()`.
- **Fallback extraction** — when Marker fails, pages are rasterised to PNG via PyMuPDF and a placeholder Markdown is generated with every image embedded.
- **`validate` command** — scan output for empty files, encoding errors, and broken image references.
- **`report` command** — generate a self-contained HTML report (Tailwind + Alpine.js) with KPI cards, a sortable/filterable results table, and per-file expandable logs.
- **Run logs** — every conversion is persisted as NDJSON to `data/runs/<run-name>/output.log`.
- **Generic group model** — works with any `<source>/<group>/*.pdf` tree (years, topics, departments — anything).
- **Rich terminal UI** — colourised progress bar and summary table.
- **Configurable** — override data dir, report title, and browser-open behaviour via `.env` or environment variables.

---

## Installation

### From PyPI

```bash
pip install pdf-markdown
```

### From source

```bash
git clone https://github.com/SkinnnyJay/pdf-markdown.git
cd pdf-markdown
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"   # includes pytest, ruff
```

The `pdf-markdown` command is then available in your virtual environment.

> **Note:** `marker-pdf` is a heavy dependency (PyTorch). If you only want to run the tests without a full GPU stack, mock it out — the CI workflow does this automatically.

---

## Quick Start

### 1. Convert a folder tree

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

### 2. Convert only specific groups

```bash
pdf-markdown convert --source ./archive --groups 1880,1900 --output ./transformed
```

### 3. Convert a single PDF

```bash
pdf-markdown convert --input ./archive/1880/census_1880.pdf --output ./transformed
```

Output:

```
transformed/
  1880/
    census_1880.md
    census_1880_assets/        ← images extracted by Marker (if any)
```

### 4. Convert a folder of PDFs

Point `--input` at a directory and every `*.pdf` inside it is converted. The directory name becomes the group name in the output tree.

```bash
pdf-markdown convert --input ./archive/1880 --output ./transformed
```

Output:

```
transformed/
  1880/
    census_1880.md
    report_A.md
```

Repeat `--input` to mix files and folders in one run:

```bash
pdf-markdown convert \
  --input ./archive/1880/special.pdf \
  --input ./archive/1890 \
  --input ./archive/1900 \
  --output ./transformed
```

### 5. Preview without writing

```bash
pdf-markdown convert --source ./archive --dry-run
```

### 6. Validate output

```bash
pdf-markdown validate --output ./transformed
pdf-markdown validate --output ./transformed --strict   # broken image refs → errors
```

### 7. Generate or re-generate an HTML report

```bash
pdf-markdown report                       # most recent run
pdf-markdown report --run-name convert-2026-03-09T14-05-32
pdf-markdown report --list                # show all recorded runs
pdf-markdown report --open                # open in browser after writing
```

---

## CLI Reference

### `convert`

| Option | Default | Description |
|---|---|---|
| `--source`, `-s` | — | Root folder with `<group>/` sub-folders |
| `--groups`, `-g` | all groups | Comma-separated group names (requires `--source`) |
| `--input`, `-i` | — | Explicit PDF file or folder (repeatable) |
| `--output`, `-o` | `transformed` | Root output directory |
| `--workers`, `-w` | from env | Number of parallel workers (default: 1) |
| `--model-path` | — | Path to HuggingFace model cache (overrides env) |
| `--timeout` | `600` | Per-file Marker timeout in seconds |
| `--run-name` | auto | Custom slug used in log and report paths |
| `--html-report / --no-html-report` | `true` | Generate an HTML report after conversion |
| `--dry-run` | `false` | Show what would be processed, then exit |

### `validate`

| Option | Default | Description |
|---|---|---|
| `--output`, `-o` | required | Output directory to validate |
| `--strict` | `false` | Treat missing image references as errors |

### `report`

| Option | Default | Description |
|---|---|---|
| `--log` | — | Path to a specific `output.log` file |
| `--run-name` | — | Run name to look up in the data directory |
| `--out` | `<run_dir>/report.html` | Custom destination for the HTML file |
| `--title` | from `.env` | Override the report heading |
| `--open / --no-open` | `false` | Open in browser after writing |
| `--list` | `false` | List all recorded runs and exit |

---

## Fallback Behaviour

When `marker_single` is unavailable or exits non-zero:

1. Each page is rasterised to PNG at 150 dpi → `<output>/<group>/<stem>_assets/`.
2. A placeholder `<output>/<group>/<stem>.md` is written:

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

## Metadata API

Every converted `.md` file includes PDF metadata in a hidden HTML comment at the top. Use these helpers for custom pipelines:

```python
from pdf_markdown.markdown_metadata import embed_metadata, extract_metadata
from pdf_markdown.pdf_metadata import get_pdf_metadata

# Create / export: prepend metadata to Markdown
metadata = get_pdf_metadata(pdf_path)  # includes source_file, author, title, etc.
content = embed_metadata(metadata) + markdown_body

# Import / transform: extract metadata from existing Markdown
metadata, body = extract_metadata(md_text)
# metadata: {"source_file": "report.pdf", "author": "…", …} or None
# body: Markdown content without the metadata block
```

---

## Configuration

Copy `.env.example` to `.env` and adjust as needed:

```bash
PDF_MARKDOWN_DATA_DIR=./data          # where run logs and reports are stored
PDF_MARKDOWN_LOG_SUBDIR=runs          # sub-directory under data_dir
PDF_MARKDOWN_REPORT_TITLE=My Report   # default HTML report title
PDF_MARKDOWN_OPEN_REPORT=false        # open browser automatically after convert
PDF_MARKDOWN_WORKERS=1                # parallel workers (1 = sequential)
PDF_MARKDOWN_MODEL_PATH=              # HuggingFace model cache (HF_HOME); empty = default
```

All variables can also be set as regular environment variables; env takes priority over `.env`.

To pre-download Marker models before your first conversion (recommended for slow networks):

```bash
make setup-model
# Or with custom model path: PDF_MARKDOWN_MODEL_PATH=/data/hf make setup-model
```

---

## Development

```bash
make install-dev   # create .venv and install all dependencies
make setup-model   # pre-download Marker models (first run may take several minutes)
make check         # format (ruff) + lint
make test          # pytest
make test-cov      # pytest with coverage report
```

Useful make targets for running conversions:

```bash
make run SOURCE=./archive OUTPUT=./transformed
make run-groups SOURCE=./archive GROUPS=1880,1890 OUTPUT=./transformed
make run-input INPUT=./archive/1880/report.pdf OUTPUT=./transformed
make dry-run SOURCE=./archive
make validate OUTPUT=./transformed
make report
make report-open
make clean
```

### Project layout

```
pdf-markdown/
├── src/
│   └── pdf_markdown/
│       ├── __init__.py         # package version
│       ├── cli.py              # Typer CLI — convert / validate / report
│       ├── config.py           # .env / env-var settings
│       ├── discovery.py        # PDF file resolution
│       ├── fallback_images.py  # image extraction & placeholder Markdown
│       ├── markdown_metadata.py # embed/extract metadata in Markdown
│       ├── marker_runner.py    # marker_single subprocess wrapper
│       ├── models.py           # ConversionResult / RunSummary dataclasses
│       ├── output.py           # output path helpers & file writing
│       ├── pdf_metadata.py     # PDF metadata extraction
│       ├── report.py           # HTML report generator
│       ├── run_logger.py       # NDJSON run-log read/write
│       └── validation.py       # Markdown output validation
├── tests/
│   ├── conftest.py
│   ├── test_cli.py
│   ├── test_config.py
│   ├── test_discovery.py
│   ├── test_fallback.py
│   ├── test_markdown_metadata.py
│   ├── test_marker_runner.py
│   ├── test_models.py
│   ├── test_output.py
│   ├── test_pdf_metadata.py
│   ├── test_run_logger.py
│   └── test_validation.py
├── scripts/
│   └── validate_output.py      # standalone validation script for CI
├── .github/
│   ├── workflows/
│   │   ├── ci.yml              # test + lint on every push
│   │   └── release.yml         # PyPI publish on version tag
│   └── ISSUE_TEMPLATE/
├── .env.example
├── pyproject.toml
├── Makefile
└── README.md
```

---

## Acknowledgments

This project relies on [Marker](https://github.com/datalab-to/marker) by [Vik Paruchuri](https://github.com/VikParuchuri) and the [datalab-to](https://github.com/datalab-to) team for high-quality PDF-to-Markdown conversion. Marker does the heavy lifting — layout detection, OCR, and structured output. We're grateful for their open-source work.

---

## License

MIT — [SkinnnyJay](https://github.com/SkinnnyJay)
