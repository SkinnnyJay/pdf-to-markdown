# Contributing to pdf-markdown

Thank you for taking the time to contribute! This document explains how to get set up, what conventions the project follows, and how to submit changes.

---

## Quick start

```bash
git clone https://github.com/SkinnnyJay/pdf-markdown.git
cd pdf-markdown
make install-dev   # creates .venv and installs all dependencies
```

Run the full suite before making any changes to confirm a clean baseline:

```bash
make check   # format + lint
make test    # pytest
```

---

## Project layout

```
pdf-markdown/
├── src/pdf_markdown/      # Library source — one responsibility per module
│   ├── cli.py             # Typer CLI entrypoint (convert / validate / report)
│   ├── config.py          # .env / environment settings
│   ├── discovery.py        # PDF file resolution
│   ├── fallback_images.py  # Page rasterisation via PyMuPDF
│   ├── markdown_metadata.py # embed/extract metadata in Markdown
│   ├── marker_runner.py    # Marker subprocess wrapper
│   ├── models.py           # ConversionResult, RunSummary dataclasses
│   ├── output.py           # Path helpers and file writing
│   ├── pdf_metadata.py     # PDF metadata extraction
│   ├── report.py           # HTML report generation
│   ├── run_logger.py       # NDJSON run log serialisation
│   └── validation.py      # Output integrity checks
├── tests/                 # pytest test suite (mirrors src modules 1-to-1)
├── scripts/               # Standalone utility scripts
├── .github/               # CI workflows and issue/PR templates
├── pyproject.toml         # Package metadata, deps, ruff + pytest config
└── Makefile               # Developer convenience targets
```

---

## Development workflow

### 1. Branch naming

| Type | Pattern | Example |
|---|---|---|
| Feature | `feat/<short-description>` | `feat/batch-progress` |
| Bug fix | `fix/<short-description>` | `fix/marker-timeout` |
| Refactor | `refactor/<short-description>` | `refactor/extract-renderer` |
| Docs | `docs/<short-description>` | `docs/add-api-reference` |

### 2. Code style

- **Formatter**: `ruff format` (run via `make format`).
- **Linter**: `ruff check` (run via `make lint`).
- **Line length**: 100 characters.
- **Python version target**: 3.12+.
- Use `from __future__ import annotations` in every module.
- Prefer `X | Y` union syntax over `Optional[X]` / `Union[X, Y]`.
- All public functions and classes must have Google-style docstrings.

`make check` runs both format and lint together. CI will fail if either does not pass.

### 3. Tests

- Every new module or feature must ship with corresponding tests under `tests/`.
- Test files mirror source modules: `src/pdf_markdown/foo.py` → `tests/test_foo.py`.
- Use `pytest` fixtures and `unittest.mock.patch` for subprocess/IO isolation.
- Do **not** require Marker or a GPU to be present in tests — mock `run_marker`.

```bash
make test          # run all tests
make test-cov      # run with coverage report
```

### 4. Commits

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add --parallel flag for concurrent PDF conversion
fix: handle marker_single timeout on large files
docs: update README quickstart
chore: bump ruff to 0.5.0
```

### 5. Pull requests

- Fill in the PR template (`.github/PULL_REQUEST_TEMPLATE.md`).
- Keep PRs focused — one feature or fix per PR.
- Ensure `make check && make test` pass locally before opening the PR.
- CI must be green before merge.

---

## Adding a new module

1. Create `src/pdf_markdown/<module>.py` with a module-level docstring and `__all__`.
2. Add the corresponding `tests/test_<module>.py`.
3. Export public symbols from `__init__.py` if they form part of the library API.
4. Add a short entry to `CHANGELOG.md` under `[Unreleased]`.

---

## Releasing a new version

**Before first release:** Create a `release` environment in GitHub (Settings → Environments). Configure PyPI trusted publishing: add the repository to [PyPI's trusted publishers](https://docs.pypi.org/trusted-publishers/) with the workflow `release.yml` and environment `release`.

1. Update `version` in `pyproject.toml`.
2. Add a release section to `CHANGELOG.md` with the date.
3. Commit: `chore: release v0.2.0`.
4. Tag: `git tag v0.2.0 && git push origin v0.2.0`.
5. The `release.yml` workflow will build and publish to PyPI automatically.

---

## Reporting issues

Use the GitHub issue templates:

- **Bug report** — for unexpected behaviour.
- **Feature request** — for new ideas or improvements.

Please include your OS, Python version, `pdf-markdown --version`, and a minimal reproduction.

---

## License

By contributing you agree that your contributions will be licensed under the project's [MIT License](LICENSE).
