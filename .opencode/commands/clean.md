---
description: Clean Python build artifacts
---
Clean Python build artifacts from the project (excluding .venv):

- Remove `__pycache__/` directories
- Remove `*.pyc` files
- Remove `*.egg-info/` directories
- Remove `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/`

Use: `find . -type d \( -name __pycache__ -o -name '*.egg-info' -o -name .pytest_cache -o -name .mypy_cache -o -name .ruff_cache \) -not -path './.venv/*' -exec rm -rf {} + 2>/dev/null; find . -type f -name '*.pyc' -not -path './.venv/*' -delete`
