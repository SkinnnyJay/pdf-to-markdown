# Code Review

## Overview

Review current changes for quality, correctness, and project conventions. Report findings with clear severity and file:line references.

## Steps

1. **Inspect changes**
   - Run `git diff` to see all changes

2. **Review against criteria**
   - Logic errors, edge cases, error handling
   - Typing: annotations on public APIs, no unjustified `# type: ignore`
   - Config via `Settings`; no raw `os.environ` or hardcoded paths
   - Ruff compliance: `make check` passes
   - Docstrings on public functions/classes
   - Functions under ~80 lines, files under ~400 lines

3. **Report findings**
   - Use severity: MUST FIX, SHOULD FIX, SUGGESTION
   - Include file:line references

## Review Checklist

- [ ] Logic and edge cases reviewed
- [ ] Naming and style match project conventions (snake_case, ruff)
- [ ] No inappropriate type ignores
- [ ] Config via Settings
- [ ] Size limits considered
