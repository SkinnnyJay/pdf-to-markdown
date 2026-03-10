# Format and Lint

## Overview

Fix all linting and formatting issues. Use make commands and follow the fixing workflow (see project rules).

## Steps

1. **Run check**
   - Run `make check` to discover ALL issues (format + lint)

2. **Auto-fix**
   - Run `make format` then `make lint-fix` to fix what can be auto-fixed

3. **Create task list**
   - Run `make check` again
   - Catalog every remaining error: file path, rule, description
   - Mark all items as pending

4. **Fix issues systematically**
   - Fix one issue at a time
   - Verify with: `ruff check <file>` or `ruff format <file>`
   - Mark done only after it passes

5. **Full confirmation**
   - Run `make check`

## Checklist

- [ ] Auto-fix applied (make format, make lint-fix)
- [ ] All remaining issues cataloged
- [ ] Each issue fixed and verified
- [ ] make check passes
