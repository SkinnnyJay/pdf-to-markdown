# Validate Output

## Overview

Validate converted Markdown output. This project has no Playwright/E2E tests; use the validate command instead.

## Steps

1. **Validate output**
   - Run `make validate OUTPUT=<path>` to check converted Markdown
   - Or: `make validate-strict OUTPUT=<path>` for strict mode (missing images → errors)

2. **Interpret results**
   - Exit 0: all files valid
   - Exit 1: errors or (in strict mode) missing image refs

## Make Targets

- `make validate` — validate output directory
- `make validate-strict` — fail on missing image references
- `make validate-script` — run standalone script with optional `ARGS=--json`
