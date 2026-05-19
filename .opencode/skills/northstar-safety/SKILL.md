---
name: northstar-safety
description: Apply Northstar Research safety doctrine for PostgreSQL source-of-truth, Neo4j derived graph writes, extraction gates, cleanup gates, backups, imports, and destructive operations.
compatibility: opencode
---

## Safety doctrine

- PostgreSQL is the source of truth.
- Neo4j is derived.
- ChromaDB/vector data is derived or rebuildable unless documented otherwise.
- Imports require explicit promotion.
- Extraction must not silently write graph data.
- Cleanup must default to dry-run or read-only.
- Destructive operations require explicit flags.
- Risky operations require backup/export validation.
- Scripts must print what they will affect before making changes.
- Avoid silent automatic mutation.

## Use this skill when touching

- migrations
- cleanup code
- extraction code
- graph writes
- import/promotion code
- delete/merge/prune scripts
- backup/restore docs
- environment flags
- source-of-truth boundaries

## Required final review

Report:

- safety risk level
- source-of-truth impact
- derived-data impact
- destructive-action safeguards
- backup requirement
- tests needed
