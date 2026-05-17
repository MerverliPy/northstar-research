# Project Ledger

This file intentionally separates documented baseline state from live runtime state. Always verify current values through the portal and watcher.

## Documented manual v1 baseline

- Completed projects: 7
- Projects with Neo4j graphs: 7
- Eligible projects needing extraction: 0
- Average graph quality score: 97
- Cleanup issue groups: 0
- Duplicate relationship candidates: 0
- Orphan cleanup candidates: 0
- Destructive cleanup: disabled

## Later session note

Session memory indicates a later Project 9 extraction event with a clean quality result. Because the uploaded excerpts do not fully describe Project 8, this repository scaffold does not hard-code a complete 1-9 ledger. Use the live watcher and quality reports as the authoritative current ledger.

## Current-state command

```bash
./check-auto-extract-eligibility.sh
curl -fsS http://127.0.0.1:8099/knowledge/quality/report -o graph-quality-global-latest.json
```
