# 🌟 Northstar OpenCode Workflow Guide

> Low-token operating guide for humans and coding agents working in Northstar Research.

<p align="center">
  <strong>Northstar Research</strong><br>
  Local AI research system · PostgreSQL source of truth · Neo4j graph layer · Ollama/self-hosted LLMs · ChromaDB vector search
</p>

<p align="center">
  <code>lowest-token-first</code> · <code>safety-gated</code> · <code>agent-routed</code> · <code>test-verified</code>
</p>

---

## 🧭 Agent-callable next-step router

Coding agents should read this section first when the next step is unclear.

### NEXT_STEP_ROUTER_V1

| Field | Value |
|---|---|
| Router | northstar-next-step-router |
| Read budget | Read this section first; expand only when needed |
| Default mode | lowest-token-safe |
| Broad repo scan | Avoid unless the router cannot identify the affected flow |
| Fallback command | /northstar-agent-audit `<one-sentence scope>` |
| Output contract | NEXT_STEP_CARD |

### Flow router

| Affected flow | First read | Best agent | Next action | Validation |
|---|---|---|---|---|
| Unknown / ambiguous | This guide, then docs/ARCHITECTURE.md only if needed | @codebase-cartographer | Map smallest relevant files | /northstar-agent-audit `<scope>` |
| LLM extraction, prompts, Ollama, embeddings | Relevant extraction/vector files only | @llm-extraction-engineer | Check structured output, hallucination risk, retries, source attribution | make VENV="$PWD/.venv/bin" test |
| Import, staging, promotion, lineage | Affected repositories/models/routes | @data-pipeline-reviewer | Protect PostgreSQL source-of-truth and derived-store sync | make VENV="$PWD/.venv/bin" test |
| FastAPI route or frontend API client | route, schema, client, tests | @api-contract-reviewer + @api-test-engineer | Preserve request/response shape and tests | make VENV="$PWD/.venv/bin" test |
| SQLAlchemy, Alembic, indexes, pagination | model, migration, repository, query call sites | @db-ops + @db-performance-reviewer | Check migrations, query bounds, indexes, async sessions | targeted DB tests + full tests |
| Neo4j / graph projection | graph service and extraction flow | @safety-guardian + @data-pipeline-reviewer | Verify graph is rebuildable and gated | graph/extraction tests |
| ChromaDB / vector search | vector package, embedding service, search route | @llm-extraction-engineer + @performance-benchmarker | Verify batch behavior and score normalization | vector/search tests |
| React/Vite portal UI | changed component/page/router only | @ui-polisher + @accessibility-auditor | Improve UX without breaking API contracts | make portal-build |
| PWA/offline/installability | Vite config, manifest, service worker, app shell | @pwa-auditor | Check install/update/offline UX | make portal-build |
| Docker, health, setup, backup/restore | Docker/ops scripts/docs only | @ops-reliability-reviewer | Check local-first reliability and rollback | docker compose -f docker/docker-compose.yml config |
| Security, scraping, exports, logs, secrets | exact risky files only | @appsec-reviewer + @safety-guardian | Check SSRF, XSS, secret leaks, destructive flags | make check-secrets + tests |
| Performance-sensitive flow | smallest benchmarkable path | @performance-benchmarker | Define baseline before optimizing | targeted benchmark + tests |
| Documentation-only | relevant doc plus source it describes | @docs-syncer | Keep docs accurate and actionable | markdown review |

### NEXT_STEP_CARD

Agents should answer with this compact card before broad repo reading:

NEXT_STEP_CARD  
scope: `<one sentence>`  
affected_flow: `<flow from router>`  
agent_to_use: `<one or two agents max>`  
files_to_read_first:  
- `<path>`  
- `<path>`  
do_not_read_yet:  
- `<broad directories to avoid>`  
validation:  
- `<exact command>`  
stop_condition: `<when to pause for user or tests>`  
token_mode: lowest-token-safe

### Minimal agent call

Read only docs/opencode-workflow-guide.md#agent-callable-next-step-router.  
Return a NEXT_STEP_CARD for: `<task>`.  
Do not scan the repo unless the card says it is required.

### Minimal command call

/northstar-agent-audit `<one-sentence description of the planned change>`

---

## ✨ Workflow map

```mermaid
flowchart LR
    A[Idea or bug] --> B{Known affected flow?}
    B -- No --> C[@codebase-cartographer]
    C --> D[NEXT_STEP_CARD]
    B -- Yes --> D[NEXT_STEP_CARD]
    D --> E[Smallest file read]
    E --> F[Targeted edit or review]
    F --> G[Specialist agent review]
    G --> H[Validation command]
    H --> I{Pass?}
    I -- No --> J[Patch narrowly]
    J --> H
    I -- Yes --> K[Commit + push]
```

---

## 🚦 Operating modes

| Mode | Use when | Context budget | Agent behavior |
|---|---|---:|---|
| 🟢 Scout | You need direction | Tiny | Read router and return NEXT_STEP_CARD only |
| 🔵 Patch | You know the files | Small | Read changed files and direct dependencies |
| 🟣 Review | Code changed | Small/medium | Use one specialist reviewer; two only if risk spans domains |
| 🟠 Safety Gate | Data, graph, cleanup, scraping, secrets | Medium | Use @safety-guardian or @appsec-reviewer before shipping |
| 🔴 Broad Map | Architecture is unclear | Controlled | Use @codebase-cartographer; avoid full repo dumps |

---

## 🧩 Northstar agent map

### Core agents

| Agent | Use for |
|---|---|
| @review | General code review and implementation review |
| @test-fix | Failing tests and targeted test repair |
| @qa-verifier | Verification after changes |
| @safety-guardian | Data loss, destructive actions, extraction gates, graph safety |
| @docs-syncer | Keeping docs aligned with behavior |
| @db-ops | Database migrations and DB operations |
| @docker | Docker Compose and container runtime issues |
| @api-contract-reviewer | FastAPI/frontend API compatibility |
| @ui-polisher | Visual polish and usability |
| @pwa-auditor | PWA installability/offline/update UX |

### Specialist agents

| Agent | Best trigger | Token-saving rule |
|---|---|---|
| @llm-extraction-engineer | LLM extraction, structured output, embeddings, ChromaDB | Read only extraction/vector/model files involved |
| @data-pipeline-reviewer | Import, staging, promotion, PostgreSQL records, derived-store sync | Start from the affected flow, not all models |
| @api-test-engineer | Route/client/test changes | Pair with @api-contract-reviewer only when contracts may shift |
| @db-performance-reviewer | Query plans, indexes, Alembic, pagination | Inspect only changed queries and callers |
| @appsec-reviewer | SSRF, XSS, CORS, logs, secrets, exports, scraping | Review risk surfaces only |
| @performance-benchmarker | Latency, throughput, extraction speed, vector/graph/search speed | Require a baseline before optimizing |
| @accessibility-auditor | Keyboard flow, forms, tables, modals, graph UI, mobile | Do not rewrite visual design wholesale |
| @codebase-cartographer | Unknown flow or onboarding | Produce a file map, not a giant summary |
| @ops-reliability-reviewer | Docker, health scripts, backup/restore, ports, logs | Do not mutate production-like data |

---

## 🛠️ Common workflows

### Small bug fix

1. Use NEXT_STEP_CARD.
2. Read only the named files.
3. Patch the smallest cause.
4. Run the narrow test first.
5. Run full tests if behavior changed.

### API change

1. Ask @api-contract-reviewer to inspect request/response compatibility.
2. Ask @api-test-engineer for missing tests.
3. Edit route/schema/client/tests together.
4. Run: make VENV="$PWD/.venv/bin" test

### Extraction or graph change

1. Use @safety-guardian first if graph writes, cleanup, or destructive flags are involved.
2. Use @llm-extraction-engineer for extraction quality.
3. Use @data-pipeline-reviewer if PostgreSQL, Neo4j, or ChromaDB consistency can change.
4. Run tests before commit.

### UI or PWA change

1. Use @ui-polisher for visual hierarchy and UX.
2. Use @accessibility-auditor for keyboard, ARIA, focus, forms, tables, and graph UI.
3. Use @pwa-auditor for installability/offline/update shell behavior.
4. Run: make portal-build

### Ops or setup change

1. Use @ops-reliability-reviewer.
2. Read only changed Docker, scripts, docs, or config files.
3. Run: docker compose -f docker/docker-compose.yml config
4. Run: make check-secrets

---

## 🧪 Validation ladder

| Change type | First check | Full check |
|---|---|---|
| Docs only | Review rendered Markdown | Related test only if docs changed behavior |
| Python logic | Targeted pytest | make VENV="$PWD/.venv/bin" test |
| Python style/imports | make VENV="$PWD/.venv/bin" lint | lint + test |
| Secrets/safety | make check-secrets | secret check + tests |
| Docker/ops | docker compose -f docker/docker-compose.yml config | health/doctor scripts if applicable |
| Portal UI | relevant UI check | make portal-build |
| API contract | targeted API tests | full test suite |
| Extraction/vector/graph | targeted extraction/vector/graph tests | full test suite + safety review |

Recommended pre-push sequence:

1. make VENV="$PWD/.venv/bin" lint
2. make VENV="$PWD/.venv/bin" test
3. make check-secrets

---

## 🧠 Lowest-token rules

### Always do

- Start with NEXT_STEP_CARD when the next step is unclear.
- Read the smallest file set that can answer the question.
- Prefer changed files, direct callers, direct tests, and one architecture doc.
- Use one specialist agent by default.
- Add a second specialist only when risk crosses domains.
- Stop after a failing validation command and report the exact failure.

### Do not do

- Do not load all of apps/, packages/, or docs/ by default.
- Do not call every specialist agent.
- Do not read .env or secret-bearing files.
- Do not run destructive cleanup, restore, migration, or graph extraction without explicit approval.
- Do not claim a change is bug-free; report validations actually run.

---

## 🧯 Safety gates

| Risk | Required behavior |
|---|---|
| Destructive cleanup | Must remain behind ENABLE_DESTRUCTIVE_CLEANUP and explicit approval |
| Graph extraction | Must remain behind FORCE_GRAPH_EXTRACTION or explicit force path |
| Chat import promotion | Must remain behind PROMOTION_ENABLED |
| PostgreSQL changes | Treat PostgreSQL as authoritative |
| Neo4j / ChromaDB divergence | Rebuild derived projections from controlled source data |
| Secrets | Never print or commit secret values |
| Backup/restore | Confirm rollback path before destructive restore |
| Scraping | Check SSRF, timeouts, allow/deny assumptions, and untrusted content handling |

---

## 📌 Commit checklist

- [ ] NEXT_STEP_CARD was used if scope was unclear.
- [ ] Only necessary files were read.
- [ ] Correct specialist agent reviewed risky work.
- [ ] Destructive or external effects were avoided or explicitly approved.
- [ ] Validation commands passed.
- [ ] Docs were updated if behavior changed.
- [ ] No secrets were read, printed, or committed.

---

## 🏁 Golden path

NEXT_STEP_CARD  
→ smallest targeted read  
→ one specialist agent  
→ focused patch  
→ cheapest valid check  
→ broader validation only when needed  
→ commit  
→ push

This is the default Northstar OpenCode workflow: safe, focused, reviewable, and low-token.
