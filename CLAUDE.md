# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Does

pdf-markdown is a Python CLI that converts PDFs to Markdown using [Marker](https://github.com/datalab-to/marker). When Marker fails, it falls back to rasterising pages as PNG images via PyMuPDF and generating placeholder Markdown with embedded images. It also produces NDJSON run logs and self-contained HTML reports.

## Common Commands

```bash
# Setup
make install-dev          # create .venv and install with dev deps

# Quality
make check                # ruff format + lint (full quality gate)
make lint-fix             # auto-fix safe lint issues

# Tests
make test                 # run pytest
make test-cov             # pytest with coverage
.venv/bin/pytest tests/test_discovery.py           # single test file
.venv/bin/pytest tests/test_discovery.py::test_name -v  # single test

# Run the CLI
.venv/bin/pdf-markdown convert --source ./archive --output ./transformed
.venv/bin/pdf-markdown validate --output ./transformed
.venv/bin/pdf-markdown report --list
```

## Architecture

The CLI is built with **Typer** (Rich markup mode) and has three commands: `convert`, `validate`, `report`. Entry point: `pdf_markdown/cli.py` → `app`.

**Conversion pipeline** (`cli.py:_convert_one`):
1. `discovery.py` resolves PDF inputs into `(group, path)` pairs — supports `--source` (folder tree), `--groups` (filter), and `--input` (explicit files/dirs)
2. `marker_runner.py` runs `marker_single` as a subprocess in a temp directory
3. On success → `output.py:copy_marker_output` moves Marker's `.md` + assets to the output tree
4. On failure → `fallback_images.py` rasterises pages to PNG, `generate_placeholder_markdown` creates a fallback `.md`
5. `pdf_metadata.py:get_pdf_metadata` extracts PDF metadata; `markdown_metadata.py:embed_metadata` prepends it as an HTML comment block
6. `models.py:ConversionResult` captures per-file results; `RunSummary` aggregates the run
7. `run_logger.py` persists results as NDJSON to `data/runs/<run-name>/output.log`
8. `report.py` generates a self-contained HTML report (Tailwind + Alpine.js)

**Output tree structure**: `<output>/<group>/<stem>.md` with optional `<stem>_assets/` for images.

**Config** (`config.py:Settings`): reads from `.env` and environment variables (prefix `PDF_MARKDOWN_`).

## Code Conventions

- **Python ≥ 3.12** required. Uses `X | Y` union syntax, not `Optional`/`Union`.
- **Ruff** for formatting and linting. Line length: 100. See `[tool.ruff]` in `pyproject.toml` for rule selection.
- `B008` is ignored (Typer uses default argument expressions like `typer.Option(...)`).
- Build system: **Hatchling** with flat layout (`pdf_markdown/`).
- Tests use `tmp_path` and `tmp_pdf` fixture (defined in `conftest.py`). Marker is mocked via subprocess mock — marker-pdf is not installed in CI.
- CI skips `marker-pdf` installation (heavy ML/PyTorch dependency) and installs runtime deps individually instead.
