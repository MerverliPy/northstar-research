SHELL := /usr/bin/env bash

.PHONY: doctor health check-secrets lint tree install install-all test portal-dev portal-build

doctor:
	@scripts/doctor.sh

health:
	@scripts/check-health.sh

check-secrets:
	@scripts/verify-no-secrets.sh

lint:
	@ruff check packages/ apps/ scripts/

tree:
	@find . -type f \( -name '*.py' -o -name '*.toml' -o -name '*.yml' -o -name '*.yaml' -o -name '*.ini' -o -name '*.sh' -o -name '*.md' -o -name '*.env*' \) \
		! -path './.venv/*' ! -path './__pycache__/*' ! -path './*/egg-info/*' ! -path './*/__pycache__/*' \
		| sort

install:
	@pip install -e packages/northstar-models
	@pip install -e packages/northstar-llm
	@pip install -e packages/northstar-vector
	@pip install -e packages/northstar-db

install-all: install
	@pip install -e apps/research-agent
	@pip install -e apps/chat-import-bridge
	@pip install -e apps/research-portal

test:
	@pytest tests/ -v

portal-dev:
	@cd apps/research-portal/research_portal/spa && npm run dev

portal-build:
	@cd apps/research-portal/research_portal/spa && npm run build
