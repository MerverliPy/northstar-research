# OpenCode Agents and Skills Guide

This repository includes a project-local OpenCode setup under `.opencode/`.

Use this guide to understand what each agent and skill is for, when to call it, and how to combine them during normal development.

## Directory layout

```text
.opencode/
  agents/
    ui-polisher.md
    pwa-auditor.md
    api-contract-reviewer.md
    safety-guardian.md
    qa-verifier.md
    docs-syncer.md
  skills/
    ui-ux-polish/
      SKILL.md
    pwa-readiness/
      SKILL.md
    api-contract-safety/
      SKILL.md
    northstar-safety/
      SKILL.md
```

## How OpenCode uses these files

Agents define specialized roles, permissions, and operating procedures. Use agents when you want OpenCode to behave like a focused reviewer, implementer, auditor, or verifier.

Skills define reusable instruction sets. Agents can load skills to apply a consistent checklist, such as UI/UX polish, PWA readiness, API contract safety, or Northstar safety doctrine.

In normal use:

- Call agents directly with `@agent-name`.
- Ask an agent to load or use a skill by name.
- Use the smallest agent that fits the task.
- Use `qa-verifier` after implementation changes.
- Use `safety-guardian` before risky data, cleanup, extraction, migration, or graph-related changes.

## Agents

### `@ui-polisher`

Use this for visual UI and usability improvements.

Best for:

- Improving the React portal UI.
- Applying `DESIGN.md` to existing components.
- Improving layout, spacing, typography, hierarchy, responsive behavior, empty states, loading states, error states, buttons, inputs, cards, navigation, and accessibility.
- Making the PWA feel more app-like without changing PWA internals.

Primary skills:

- `ui-ux-polish`
- `pwa-readiness`

Example prompts:

```text
@ui-polisher read DESIGN.md and improve the portal UI. Keep business logic and API contracts unchanged.
```

```text
@ui-polisher use the ui-ux-polish skill and polish the dashboard, sidebar, tables, forms, empty states, and loading states.
```

```text
@ui-polisher review the current PWA UI for mobile-first usability, touch targets, spacing, and accessibility. Make safe visual improvements only.
```

### `@pwa-auditor`

Use this for PWA-specific review and improvements.

Best for:

- Auditing `vite-plugin-pwa` usage.
- Reviewing manifest quality.
- Reviewing service-worker registration and update UX.
- Checking installability assumptions.
- Reviewing offline/reconnect/loading/error states.
- Checking app-shell behavior and standalone display mode UX.
- Reviewing touch targets, mobile safe areas, and mobile-first layout.

Primary skills:

- `pwa-readiness`
- `ui-ux-polish`

Example prompts:

```text
@pwa-auditor audit the React/Vite PWA setup and list installability, offline UX, manifest, and app-shell issues. Do not edit files yet.
```

```text
@pwa-auditor use the pwa-readiness skill and improve safe offline, loading, reconnect, and update UX without changing API contracts.
```

```text
@pwa-auditor inspect vite.config.ts, index.html, src/main.tsx, App.tsx, router files, layout components, and public icons. Report remaining PWA risks.
```

### `@api-contract-reviewer`

Use this when frontend or backend changes may affect API compatibility.

Best for:

- FastAPI route changes.
- Frontend API client changes.
- Form, CRUD, import, promotion, extraction, cleanup, graph, search, and quality-scoring flows.
- Request/response schema review.
- Status code and error response review.
- Backward-compatibility checks.

Primary skill:

- `api-contract-safety`

Example prompts:

```text
@api-contract-reviewer review the changes to the project/source/entity/claim/report flows and confirm no API contracts were broken.
```

```text
@api-contract-reviewer inspect this frontend data-fetching change against the matching FastAPI routes and Pydantic models.
```

```text
@api-contract-reviewer use api-contract-safety and identify any request/response shape, status-code, or endpoint-path risks before implementation.
```

### `@safety-guardian`

Use this before risky changes. This is a reviewer-only agent and should not edit files.

Best for:

- PostgreSQL source-of-truth changes.
- Neo4j graph writes or rebuilds.
- ChromaDB/vector changes.
- Extraction jobs.
- Cleanup jobs.
- Migrations.
- Imports and promotions.
- Backup/restore behavior.
- Destructive scripts.
- Environment flags.
- Secret handling.

Primary skill:

- `northstar-safety`

Example prompts:

```text
@safety-guardian review this cleanup change for Northstar safety doctrine violations. Do not edit files.
```

```text
@safety-guardian use northstar-safety and assess the risk of this migration, including source-of-truth, backup, and destructive-action safeguards.
```

```text
@safety-guardian inspect this graph extraction change and confirm it does not silently mutate derived graph data.
```

### `@qa-verifier`

Use this after code changes to run or recommend the correct verification path.

Best for:

- Running targeted checks after implementation.
- Interpreting lint, test, and build failures.
- Choosing the smallest meaningful verification set.
- Avoiding broad, unrelated refactors.

Typical check matrix:

| Change type | Suggested verification |
|---|---|
| Python-only | `make lint`, `make test` |
| Portal SPA | `cd apps/research-portal/research_portal/spa && npm run lint`, `cd apps/research-portal/research_portal/spa && npm run build`, or `make portal-build` |
| Cross-service | `make lint`, `make test`, `make portal-build` |

Example prompts:

```text
@qa-verifier inspect the changed files and run the smallest meaningful verification set.
```

```text
@qa-verifier run portal lint/build checks and explain any failures precisely.
```

```text
@qa-verifier after these backend changes, run the relevant Python checks and identify the exact next fix if anything fails.
```

### `@docs-syncer`

Use this when code changes should be reflected in documentation.

Best for:

- README updates.
- `DESIGN.md` updates.
- Architecture docs.
- API docs.
- Safety docs.
- Setup and operations docs.
- PWA behavior docs.
- Service port, CLI, or environment flag changes.

Example prompts:

```text
@docs-syncer inspect the current changes and update only the docs affected by behavior changes.
```

```text
@docs-syncer check whether README, API docs, architecture docs, and safety docs need updates after this feature.
```

```text
@docs-syncer document this new PWA behavior without inventing features or changing unrelated docs.
```

## Skills

### `ui-ux-polish`

Reusable checklist for UI improvement work.

Use for:

- Layout polish.
- Spacing rhythm.
- Typography scale.
- Visual hierarchy.
- Color and contrast.
- Responsive layout.
- Forms, buttons, cards, tables, modals, and navigation.
- Empty, loading, and error states.
- Accessibility checks.
- PWA-specific UI/UX checks when applicable.

Common use:

```text
@ui-polisher use the ui-ux-polish skill and improve the selected view without changing app logic.
```

### `pwa-readiness`

Reusable checklist for PWA review and improvement.

Use for:

- Vite PWA setup.
- Manifest review.
- Service-worker and Workbox review.
- Installability assumptions.
- Offline/reconnect/update UX.
- App-shell behavior.
- Mobile-first layout and safe-area handling.

Common use:

```text
@pwa-auditor use the pwa-readiness skill and audit installability, offline UX, update UX, and app-shell behavior.
```

### `api-contract-safety`

Reusable checklist for API compatibility.

Use for:

- Endpoint path preservation.
- HTTP method preservation.
- Request and response schema preservation.
- Status code and error behavior review.
- Frontend/backend integration safety.
- Pydantic model and FastAPI route alignment.

Common use:

```text
@api-contract-reviewer use api-contract-safety and review this frontend/backend change for compatibility risks.
```

### `northstar-safety`

Reusable checklist for this repository's safety doctrine.

Use for:

- PostgreSQL source-of-truth boundaries.
- Neo4j as derived data.
- ChromaDB/vector derived-data assumptions.
- Cleanup dry-run behavior.
- Extraction gates.
- Destructive-action safeguards.
- Backup/export validation expectations.
- No silent mutation of important data.

Common use:

```text
@safety-guardian use northstar-safety and review this migration, cleanup, extraction, or graph-related change.
```

## Recommended workflows

### UI polish workflow

```text
@ui-polisher read DESIGN.md, load ui-ux-polish, and propose a prioritized UI polish plan. Do not edit files yet.
```

Then:

```text
@ui-polisher implement the top-priority safe UI improvements. Keep backend logic, API contracts, and PWA caching behavior unchanged.
```

Then:

```text
@qa-verifier inspect the changed files and run the relevant portal checks.
```

### PWA audit workflow

```text
@pwa-auditor use pwa-readiness and audit the current PWA setup. Do not edit files yet.
```

Then:

```text
@pwa-auditor implement only low-risk UX improvements for offline, reconnect, loading, update, safe-area, and standalone-app experience.
```

Then:

```text
@qa-verifier run the portal lint/build verification path.
```

### API change workflow

```text
@api-contract-reviewer use api-contract-safety and review the proposed API/frontend integration change before edits.
```

Then:

```text
@qa-verifier run the relevant Python and portal checks for the changed files.
```

Then:

```text
@docs-syncer update only the API or operational docs affected by the behavior change.
```

### Risky data or cleanup workflow

```text
@safety-guardian use northstar-safety and review the planned migration, cleanup, extraction, graph write, or destructive script. Do not edit files.
```

If the safety review passes:

```text
@api-contract-reviewer check whether this change affects any endpoint contracts or frontend assumptions.
```

Then:

```text
@qa-verifier run the smallest meaningful verification set.
```

### Documentation sync workflow

```text
@docs-syncer inspect the changed files and update README, DESIGN.md, API docs, architecture docs, or safety docs only where behavior changed.
```

Then:

```text
@qa-verifier inspect documentation-only changes and confirm no runtime verification is needed.
```

## Practical rules

- Use `@ui-polisher` for visual UI changes.
- Use `@pwa-auditor` for installability, offline, app-shell, and mobile PWA behavior.
- Use `@api-contract-reviewer` before changing API routes, schemas, or frontend API usage.
- Use `@safety-guardian` before changing anything that can mutate, delete, rebuild, import, promote, extract, migrate, or affect source-of-truth data.
- Use `@qa-verifier` after implementation changes.
- Use `@docs-syncer` when behavior changes need documentation updates.
- Prefer review/planning prompts before implementation prompts for high-risk changes.
- Keep agents focused: do not ask one agent to do design, backend contracts, safety review, docs sync, and QA in one pass.

## Example one-line prompts

```text
@ui-polisher polish the Sources view using DESIGN.md and ui-ux-polish. Keep app logic unchanged.
```

```text
@pwa-auditor audit the portal PWA for offline, installability, update UX, and mobile safe-area issues.
```

```text
@api-contract-reviewer review this CRUD change for endpoint, schema, status-code, and error-shape compatibility.
```

```text
@safety-guardian assess this cleanup/extraction change against Northstar safety doctrine. Do not edit files.
```

```text
@qa-verifier run the smallest relevant verification set for the current diff.
```

```text
@docs-syncer update docs affected by this behavior change and leave unrelated docs untouched.
```

<!-- BEGIN GENERATED NORTHSTAR AGENT ADAPTATIONS -->

## Adapted specialist agents

These agents were adapted from the GitHub agent-pack review and narrowed to Northstar-specific workflows. Use the smallest relevant agent; do not invoke all agents for routine work.

### `@llm-extraction-engineer`

Use for local LLM extraction, embeddings, vector search, ChromaDB behavior, quality scoring, structured model output, and Ollama/self-hosted model concerns.

### `@data-pipeline-reviewer`

Use for import, staging, promotion, PostgreSQL canonical persistence, source lineage, derived Neo4j/ChromaDB sync, cleanup, backup/restore, and data-quality invariants.

### `@api-test-engineer`

Use for FastAPI endpoint tests, frontend/backend contract tests, async mocks, safety-gate tests, extraction/cleanup/search/graph/report coverage, and regression test planning.

### `@db-performance-reviewer`

Use for SQLAlchemy async repository performance, Alembic migration performance, indexes, query shape, pagination, Neo4j graph query performance, and unbounded-list risks.

### `@appsec-reviewer`

Use before changes involving scraping, untrusted rendered content, imports/exports, logs, CORS, secrets, public exposure, destructive flags, or safety bypasses.

### `@performance-benchmarker`

Use for safe benchmark design around extraction latency, vector search, graph queries, API latency, portal build/runtime behavior, and large import/export flows.

### `@accessibility-auditor`

Use for React/Vite portal accessibility, keyboard flow, semantics, forms, tables, modals, graphs, mobile usability, PWA affordances, and reduced-motion behavior.

### `@codebase-cartographer`

Use before large or ambiguous tasks to map the smallest relevant files, flows, service boundaries, tests, and recommended follow-up agents.

### `@ops-reliability-reviewer`

Use for Docker Compose, service health, doctor scripts, systemd units, backup/restore, logs, ports, and local-first reliability reviews.

### `/northstar-agent-audit`

Use this command when you want OpenCode to select the smallest relevant subset of adapted agents for a scoped audit.

<!-- END GENERATED NORTHSTAR AGENT ADAPTATIONS -->
