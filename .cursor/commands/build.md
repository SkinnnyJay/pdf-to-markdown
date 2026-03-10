# Build Project

## Overview

Build the Python package (wheel + sdist) and fix any errors.

## Steps

1. **Install build tools**
   - `pip install hatchling build`

2. **Run build**
   - Run `python -m build` to discover errors

3. **Fix issues**
   - Address any build/import errors
   - Verify with `make check && make test`

4. **Confirm**
   - `python -m build` succeeds
   - Artifacts in `dist/`: `*.whl` and `*.tar.gz`

## Checklist

- [ ] python -m build passes
- [ ] dist/ contains wheel and sdist
- [ ] make check && make test pass
