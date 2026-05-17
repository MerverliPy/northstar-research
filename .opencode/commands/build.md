---
description: Install all packages and apps in editable mode
---
Run `make install-all` to install all packages and apps in editable mode.

Order enforced by Makefile:
1. northstar-models (no deps)
2. northstar-llm (depends on models)
3. northstar-vector (depends on llm)
4. northstar-db (depends on models)
5. research-agent
6. chat-import-bridge
7. research-portal

Report any installation errors.
