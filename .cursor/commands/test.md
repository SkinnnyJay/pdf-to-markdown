# Run Tests

## Overview

Execute the test suite and fix any failures. Use make commands and follow the fixing workflow.

## Steps

1. **Run test suite**
   - Run `make test` to discover ALL failures

2. **Create task list**
   - Catalog every failing test: file path, test name, short description
   - Mark all items as pending

3. **Fix issues systematically**
   - Fix one test at a time
   - Verify with: `pytest tests/<test_file>.py -v -k <test_name>`
   - Mark done only after it passes

4. **Full confirmation**
   - Run `make test` again
   - Run `make check` as final gate

## Checklist

- [ ] All test failures cataloged
- [ ] Each failure fixed and verified individually
- [ ] make test passes
- [ ] make check passes
