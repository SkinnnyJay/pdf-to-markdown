PYTHON ?= python3
VENV   := .venv
BIN    := $(VENV)/bin

.DEFAULT_GOAL := help

# ── Help ─────────────────────────────────────────────────────────────────────

.PHONY: help
help: ## Show this help
	@awk 'BEGIN{FS=":.*##"; printf "\npdf-markdown — Makefile\n\nUsage:\n  make \033[36m<target>\033[0m\n\nTargets:\n"} \
	/^[a-zA-Z_%-]+:.*##/ { printf "  \033[36m%-24s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)
	@echo ""

# ── Environment / Install ────────────────────────────────────────────────────

.PHONY: venv
venv: ## Create virtual environment
	$(PYTHON) -m venv $(VENV)
	$(BIN)/pip install --upgrade pip

.PHONY: install
install: venv ## Install package + runtime deps
	$(BIN)/pip install -e .

.PHONY: install-dev
install-dev: venv ## Install package + dev/test deps
	$(BIN)/pip install -e ".[dev]"

# ── Format / Lint ────────────────────────────────────────────────────────────

.PHONY: format
format: ## Format code with ruff
	$(BIN)/ruff format pdf_markdown/ tests/ scripts/

.PHONY: lint
lint: ## Lint code with ruff
	$(BIN)/ruff check pdf_markdown/ tests/ scripts/

.PHONY: lint-fix
lint-fix: ## Lint and auto-fix safe issues
	$(BIN)/ruff check --fix pdf_markdown/ tests/ scripts/

.PHONY: check
check: format lint ## Format then lint (full quality gate)

# ── Tests ────────────────────────────────────────────────────────────────────

.PHONY: test
test: ## Run pytest test suite
	$(BIN)/pytest

.PHONY: test-cov
test-cov: ## Run tests with coverage report
	$(BIN)/pytest --cov=pdf_markdown --cov-report=term-missing

# ── Model setup ───────────────────────────────────────────────────────────────

.PHONY: setup-model
setup-model: ## Pre-download Marker models (respects PDF_MARKDOWN_MODEL_PATH)
	$(BIN)/python scripts/setup_model.py

# ── Test data ─────────────────────────────────────────────────────────────────

.PHONY: generate-shakespeare
generate-shakespeare: ## Generate Shakespeare PDFs (COUNT=N, TEST_DATA_DIR from .env)
	$(BIN)/python scripts/generate_shakespeare_pdfs.py \
		$(if $(COUNT),--count $(COUNT),)

# ── CLI shortcuts ─────────────────────────────────────────────────────────────

.PHONY: run
run: ## Convert all groups under SOURCE= to OUTPUT=
	@# Example: make run SOURCE=/Volumes/Krusty GROUPS=1880,1890,1900,1910
	$(BIN)/pdf-markdown convert \
		--source $(or $(SOURCE), ../archive) \
		--output $(or $(OUTPUT), ../transformed)

.PHONY: run-groups
run-groups: ## Convert specific GROUPS= in SOURCE= (comma-separated)
	@# Example: make run-groups SOURCE=/Volumes/Krusty GROUPS=1880,1890,1900,1910
	$(BIN)/pdf-markdown convert \
		--source $(or $(SOURCE), ../archive) \
		--groups $(or $(GROUPS), 1880,1890,1900,1910) \
		--output $(or $(OUTPUT), ../transformed)

.PHONY: run-input
run-input: ## Convert a single PDF or folder via INPUT=
	@# Example: make run-input INPUT=../1880/report.pdf
	$(BIN)/pdf-markdown convert \
		--input $(or $(INPUT), ../sample.pdf) \
		--output $(or $(OUTPUT), ../transformed)

.PHONY: dry-run
dry-run: ## Preview what would be converted (no writes)
	$(BIN)/pdf-markdown convert \
		--source $(or $(SOURCE), ../archive) \
		--output $(or $(OUTPUT), ../transformed) \
		--dry-run

# ── Validate ──────────────────────────────────────────────────────────────────

.PHONY: validate
validate: ## Validate markdown output (pass OUTPUT=<dir>)
	$(BIN)/pdf-markdown validate \
		--output $(or $(OUTPUT), ../transformed)

.PHONY: validate-strict
validate-strict: ## Validate markdown output, fail on missing images
	$(BIN)/pdf-markdown validate \
		--output $(or $(OUTPUT), ../transformed) \
		--strict

.PHONY: validate-script
validate-script: ## Run standalone validation script (supports --json flag)
	$(BIN)/python scripts/validate_output.py $(or $(OUTPUT), ../transformed) $(ARGS)

# ── Reports ───────────────────────────────────────────────────────────────────

.PHONY: report
report: ## Generate HTML report for most recent run (or RUN=<name>)
	$(BIN)/pdf-markdown report \
		$(if $(RUN),--run-name $(RUN),) \
		$(if $(TITLE),--title "$(TITLE)",)

.PHONY: report-open
report-open: ## Generate HTML report and open in browser
	$(BIN)/pdf-markdown report \
		$(if $(RUN),--run-name $(RUN),) \
		--open

.PHONY: report-list
report-list: ## List all recorded conversion runs
	$(BIN)/pdf-markdown report --list

# ── Git / GitHub ──────────────────────────────────────────────────────────────

.PHONY: git-init
git-init: ## Initialise git repo and make first commit
	git init
	git add .
	git commit -m "chore: initial commit — pdf-markdown v0.1.0"

# ── Housekeeping ──────────────────────────────────────────────────────────────

.PHONY: clean
clean: ## Remove build artefacts and caches
	rm -rf dist/ build/ *.egg-info pdf_markdown/*.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	find . -name ".coverage" -delete 2>/dev/null || true
	rm -f coverage.xml

.PHONY: clean-all
clean-all: clean ## Remove build artefacts and the virtual environment
	rm -rf $(VENV)
