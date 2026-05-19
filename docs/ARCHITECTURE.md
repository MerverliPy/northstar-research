# Architecture

## Concept

Northstar Research is a local RAG research system with a knowledge-graph layer. The LLM provides reasoning and summarization, while durable project records, sources, reports, summaries, embeddings, and graph projections make the workflow auditable and repeatable.

## High-level flow

```text
User topic or approved chat transcript
  -> source material is stored
  -> summaries, claims, and entities are extracted
  -> PostgreSQL stores durable project records
  -> embeddings support semantic retrieval
  -> Neo4j visualizes project/entity/claim/source/report relationships
  -> portal dashboards expose quality, cleanup, watcher, and graph views
```

## Components

| Component | Role |
|---|---|
| Research Agent | Research workflow, APIs, health checks, graph extraction, quality scoring, cleanup reports. |
| PostgreSQL | Source of truth for projects, sources, reports, metadata, and durable records. |
| Neo4j | Visual relationship layer for graph views and graph quality checks. |
| Native WSL Portal | Operator UI (PWA) on local port `3010`. Offline shell, installable, SW update prompt via toast. |
| Tailscale Serve | Optional HTTPS exposure to trusted tailnet clients. |
| Watcher | Read-only reporter for completed projects without graphs. |
| Controlled Gate | Safe extraction gate that skips existing graphs, caps work, and checks quality. |
| Chat Import Bridge | Manual staging area for chat transcripts before promotion into research projects. |

## Source-of-truth rule

PostgreSQL is authoritative. Neo4j is a derived projection for visibility and relationship traversal. If the two disagree, inspect PostgreSQL first and rebuild graph projections through controlled extraction only after backup validation.
