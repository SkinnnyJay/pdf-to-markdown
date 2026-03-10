# Changelog

All notable changes to this project will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

---

## [0.1.0] — 2026-03-10

### Added
- **`convert` command** — convert PDFs to Markdown via [Marker](https://github.com/datalab-to/marker).
  - `--source` / `--groups` for folder-tree processing.
  - `--input` for explicit file or directory targets (repeatable).
  - `--dry-run` to preview without writing.
  - `--run-name` for custom run identifiers.
  - `--html-report / --no-html-report` to control report generation.
- **`validate` command** — check converted Markdown files for encoding, emptiness, and broken image refs.
  - `--strict` mode promotes missing image warnings to errors.
- **`report` command** — generate or re-generate HTML reports from past run logs.
  - `--run-name`, `--log`, `--out`, `--title`, `--open`, `--list`.
- **HTML report** (Tailwind CSS + Alpine.js via CDN):
  - Summary KPI cards (total, OK, fallback, failed, success rate, duration).
  - Sortable, filterable results table with status badges.
  - Per-row expandable log panels showing stdout/stderr/error output.
  - XSS-safe HTML escaping.
- **Run logging** — NDJSON `output.log` saved to `data/runs/<run-name>/`.
- **Fallback image extraction** — when Marker fails, rasterise pages via PyMuPDF and produce a placeholder Markdown with embedded image links.
- **`.env` / environment variable config** via `config.py`.
- Full `pytest` test suite with 70+ tests across all modules.
- `ruff` lint + format enforcement.
- `Makefile` with `install`, `install-dev`, `setup-model`, `format`, `lint`, `check`, `test`, `test-cov`, `run`, `run-groups`, `run-input`, `dry-run`, `validate`, `validate-strict`, `report`, `report-open`, `report-list`, `clean`, `clean-all`.
- GitHub Actions CI (`ci.yml`) — test matrix on Python 3.12–3.14, lint, coverage upload.
- GitHub Actions Release (`release.yml`) — PyPI trusted publishing on version tag.

[Unreleased]: https://github.com/SkinnnyJay/pdf-markdown/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/SkinnnyJay/pdf-markdown/releases/tag/v0.1.0
