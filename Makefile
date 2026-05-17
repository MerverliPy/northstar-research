SHELL := /usr/bin/env bash

.PHONY: help doctor health lint check-secrets tree

help:
	@echo "Northstar Research repository commands"
	@echo "  make doctor        Run local repo sanity checks"
	@echo "  make health        Check local service endpoints"
	@echo "  make check-secrets Verify likely secrets/runtime files are not staged"
	@echo "  make lint          Syntax-check shell scripts"
	@echo "  make tree          Print tracked scaffold tree"

doctor:
	@scripts/doctor.sh

health:
	@scripts/check-health.sh

check-secrets:
	@scripts/verify-no-secrets.sh

lint:
	@set -euo pipefail; \
	for f in scripts/*.sh; do \
	  [ -f "$$f" ] || continue; \
	  bash -n "$$f"; \
	done; \
	echo "Shell syntax checks passed."

tree:
	@find . -maxdepth 4 -type f | sort | sed 's#^./##'
