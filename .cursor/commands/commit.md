# Commit Changes

## Overview

Group changed files into logical, atomic commits using conventional commit format. Ensure quality gates pass before committing.

## Steps

1. **Review changes**
   - Run `git status` and `git diff --staged`

2. **Plan commits**
   - Group into logical, atomic commits
   - Use conventional commits: `<type>(<scope>): <summary>`
   - Types: feat, fix, chore, refactor, docs, test
   - Present tense, imperative mood, under 72 characters

3. **Quality gate**
   - Run `make check && make test` before committing

4. **Commit**
   - Stage each group and commit separately

5. **Never commit** `.env`, credentials, or secrets

## Checklist

- [ ] Changes reviewed
- [ ] Commits atomic and logically grouped
- [ ] Message format: `<type>(<scope>): <summary>`
- [ ] make check && make test pass
- [ ] No secrets or .env in commit
