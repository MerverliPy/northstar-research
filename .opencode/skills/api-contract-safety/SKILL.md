---
name: api-contract-safety
description: Preserve FastAPI/frontend API contracts while changing routes, schemas, frontend clients, forms, CRUD flows, and data-fetching behavior.
compatibility: opencode
---

## Contract rules

Preserve unless explicitly asked to change:

- HTTP methods
- endpoint paths
- request payload shapes
- response payload shapes
- status codes
- pagination/query parameters
- error response behavior
- ID formats
- field names
- required/optional fields

## Review process

1. Identify the frontend component or API client being changed.
2. Find the matching FastAPI route.
3. Find the Pydantic model or schema.
4. Check tests or docs for the same contract.
5. Prefer backward-compatible additions over breaking changes.
6. Flag any migration requirement.
7. Update docs if behavior changes.

## High-risk areas in this repo

- project/source/entity/claim/report CRUD
- import promotion
- extraction force behavior
- cleanup execution
- graph data endpoints
- vector search
- quality scoring
