---
description: Run ruff linter and fix issues
---
Run `ruff check packages/ apps/ scripts/` and fix any issues found.

Fix strategy:
1. Fix auto-fixable issues with `ruff check --fix packages/ apps/ scripts/`
2. For non-auto-fixable issues, read the relevant file and apply the fix
3. Re-run lint to verify all issues are resolved
4. Report what was fixed
