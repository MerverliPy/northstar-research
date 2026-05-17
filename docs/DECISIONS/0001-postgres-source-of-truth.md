# ADR 0001 - PostgreSQL is the source of truth

## Status

Accepted.

## Context

The system stores research projects, sources, reports, summaries, and operational metadata. A graph layer is useful for visual inspection and relationship traversal, but graph projections can be rebuilt and should not become the sole authoritative record.

## Decision

PostgreSQL remains the source of truth. Neo4j is a derived visual relationship layer.

## Consequences

- Graph extraction is treated as projection from durable records.
- Graph rebuilds require backup awareness and quality checks.
- Cleanup defaults to read-only/dry-run until explicitly reviewed.
- If PostgreSQL and Neo4j disagree, inspect PostgreSQL first.
