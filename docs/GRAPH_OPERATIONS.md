# Knowledge Graph Operations

## What goes into the graph

- Project nodes
- Entity nodes
- Claim nodes
- Source nodes
- Report nodes
- Relationships such as `HAS_ENTITY`, `HAS_CLAIM`, `HAS_SOURCE`, `HAS_REPORT`, and `SUPPORTED_BY`

## Routine graph flow

```bash
./check-auto-extract-eligibility.sh
./controlled-auto-extract-run-one.sh
```

Use the controlled gate for routine work because it skips existing graphs, caps work, records history, and runs quality checks.

## Manual extraction

```bash
~/extract-project-graph-safe.sh <project_id>
```

Use manual extraction only when intentionally extracting a project that does not already have a graph or when troubleshooting.

## Quality gates

A graph is trusted only when:

- Score is at or above the configured minimum.
- `automation_ready` is true.
- Claims are source-supported.
- Required properties are present.
- Duplicate groups remain zero.
- Cleanup reports remain clean.

## Cleanup policy

Cleanup reports and duplicate/orphan planners must remain read-only or dry-run unless a reviewed migration enables writes.
