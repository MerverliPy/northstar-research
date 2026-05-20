# LLM & Extraction Pipeline Audit

**Date**: 2026-05-20
**Scope**: `packages/northstar-llm/`, `packages/northstar-vector/`, `apps/research-agent/` (extraction, quality, search)
**Files inspected**: 18 source files, 4 test files

---

## Overall LLM Health Score: 62/100 (MEDIUM risk)

| Dimension | Score | Weight | Notes |
|-----------|-------|--------|-------|
| Prompt quality | 55/100 | 20% | Zero-shot only; no few-shot examples; no output constraints beyond schema |
| Error handling | 45/100 | 25% | HTTP errors skip retries entirely; embeddings have zero retry logic |
| Output parsing safety | 60/100 | 20% | JSON block extraction works but regex fragile; no content-anchoring validation |
| Extraction audit trail | 50/100 | 15% | Logs miss model, latency, claims count; no confidence filtering |
| Cache design | 80/100 | 10% | Key is complete; no per-operation TTL; no cache miss logging |
| Vector store integrity | 65/100 | 10% | Score normalization assumes cosine; no dimension validation; good batch support |

---

## 1. LLMService Audit (`packages/northstar-llm/northstar_llm/service.py`)

### 1.1 Prompt Construction

**File**: `service.py` lines 38–91, 133–160

The `generate()` method builds Ollama-native payloads directly — no chat-template wrapping. The `system_prompt` is set as the `"system"` key but only for the Ollama `/api/generate` endpoint. This is correct for raw completion-style calls but means the model receives system/user instructions without role separation if the client ever switches to `/api/chat`.

**Finding 1.1a — MEDIUM**: No chat-template wrapping. The raw `/api/generate` endpoint requires the prompt to embed role instructions inline. If a future model requires `/api/chat` with explicit `messages: [{"role": "system", ...}, {"role": "user", ...}]`, this pipeline silently breaks.

**Recommendation**: Abstract the payload builder to support both `/api/generate` and `/api/chat` backends, or document the raw-completion limitation explicitly.

### 1.2 Retry Logic

**File**: `service.py` lines 47–90

The retry flow has a critical design flaw:

```python
for model in models_to_try:          # outer: model loop
    for attempt in range(3):          # inner: retry loop (3 attempts)
        try:
            response = await self._call_ollama(...)
            ...
        except (httpx.TimeoutException, httpx.ConnectError, httpx.ReadError) as exc:
            # Retried up to 3x with exponential backoff: 1s, 2s
            if attempt < 2:
                await asyncio.sleep(2 ** attempt)  # 1s, 2s
            else:
                last_error = exc
                break  # exits inner retry loop, falls to next model
        except Exception as exc:
            # ANY other exception (including HTTPStatusError for 4xx/5xx)
            # → immediate break with ZERO retries
            last_error = exc
            break
```

**Finding 1.2a — CRITICAL**: `HTTPStatusError` (raised by `response.raise_for_status()` at line 158) is caught by the broad `except Exception` at line 78, NOT the transport-error block at line 66. This means **every 5xx, 429, or transient HTTP error from Ollama goes straight to the fallback model with zero retries**. Ollama frequently returns 500s under load — these should be retried.

**Finding 1.2b — LOW**: The exponential backoff uses `2 ** attempt` yielding delays of 1s, 2s for attempts 1 and 2. This is not the conventional 2^n pattern (which would be 1s, 2s, 4s). It matches the documented "3-retry exponential backoff" only loosely.

**Finding 1.2c — MEDIUM**: `generate_structured()` has no retry override and no configurable temperature/max_tokens. The extraction pipeline (which uses `generate_structured`) gets hardcoded defaults (temp=0.7, max_tokens=4096) which may be inappropriate for structured extraction (temp should be closer to 0.0–0.2 for deterministic output).

**Recommendation**: 
- Move `HTTPStatusError` into the retryable exception tuple or add explicit status-code-based retry logic.
- Expose `temperature` and `max_tokens` as parameters on `generate_structured()`.
- Consider jitter on backoff delays.

### 1.3 Output Parsing (generate_structured)

**File**: `service.py` lines 92–118

The two-stage parsing approach is:
1. Direct `json.loads(text)` on the full response
2. Regex extraction of ` ```json ... ``` ` fenced blocks

**Finding 1.3a — MEDIUM**: The regex `r"```(?:json)?\s*\n?(.*?)\n?```"` uses non-greedy `.*?` which can truncate on the first backtick triple it encounters. A response like:
```
Here is JSON: ```json {"key": "value with ``` inside"} ```
```
would match only `{"key": "value with ``, dropping the rest.

**Finding 1.3b — LOW**: Only one JSON block is attempted. If the model outputs multiple JSON blocks, the second is silently ignored.

**Finding 1.3c — MEDIUM**: No attempt to strip markdown preamble/postamble text before the first parse attempt. The direct `json.loads(text)` fails if the model says "Here is your result:\n{...}" — this case falls through to the regex extraction. A `text.find("{")` and `text.rfind("}")` approach would be more robust as a first-pass attempt.

**Recommendation**: Add a third parsing strategy — slice from first `{` to matching `}` — before the regex fallback. Consider using `json.loads` with `strict=False` or a JSON repair library for partially malformed output.

### 1.4 Hallucination Guards

**Finding 1.4 — HIGH**: There are **zero hallucination guards** anywhere in the pipeline:
- No source-content anchoring (claims are not verified against source text)
- No contradiction detection across extractions
- No confidence-threshold filtering (confidence=0.0 entities are persisted)
- No provenance chain linking extracted claims back to source spans

The `confidence` field is populated by the LLM itself — a model can hallucinate a claim and assign it confidence=0.95 with no challenge.

**Recommendation**: Implement at minimum:
1. A configurable `MIN_CONFIDENCE` threshold (default 0.3) below which entities/claims are logged but not persisted.
2. Claim-to-source anchoring via embedding similarity or substring matching.

---

## 2. EmbeddingService Audit (`service.py` lines 174–224)

### 2.1 Timeout Configuration

**File**: `service.py` line 182

```python
self._client = httpx.AsyncClient(timeout=httpx.Timeout(60.0))
```

60-second timeout is correctly configured and matches documentation.

### 2.2 Batch Embedding

**File**: `service.py` lines 200–211

`embed_batch()` sends all texts in a single Ollama `/api/embed` request. Ollama's `/api/embed` endpoint natively supports batch input via the `"input"` field accepting a list of strings.

**Finding 2.2a — CRITICAL**: There is **no error handling or retry logic** in either `embed()` or `embed_batch()`. A single timeout, connection error, or HTTP error propagates directly to the caller. Compare this with `LLMService.generate()` which has 3 retries + model fallback. This asymmetry means vector operations are the weakest link in the pipeline.

**Finding 2.2b — LOW**: `embed_batch()` does not verify that the number of returned embeddings matches the number of input texts. If Ollama drops an embedding, the VectorStore's index alignment will silently break.

**Finding 2.2c — LOW**: No batch-size limit. Sending 1000+ texts in one request could exceed Ollama's memory limit or timeout constraints.

**Recommendation**:
- Add at minimum 2 retries with backoff for transport errors.
- Validate `len(data["embeddings"]) == len(texts)` in `embed_batch()`.
- Consider a max batch size (e.g., 64) with automatic chunking.

---

## 3. Extraction Logic Audit (`apps/research-agent/research_agent/services/extraction.py`)

### 3.1 Entity Extraction

**Files**: `extraction.py` lines 33–38 (prompts), lines 52–150 (pipeline)

**Prompt analysis**:

```
EXTRACTION_SYSTEM_PROMPT = """You are a research extraction system. Extract entities and claims from the given source content.
Return ONLY valid JSON matching this schema:
{
  "entities": [{"name": "...", "entity_type": "person|organization|concept|technology|location|event|product|document|other", "description": "...", "confidence": 0.0-1.0}],
  "claims": [{"claim_text": "...", "claim_type": "...", "confidence": 0.0-1.0, "entity_name": "..."}]
}"""
```

**Finding 3.1a — MEDIUM**: Zero-shot extraction with no examples. Few-shot examples would dramatically improve extraction quality, especially for distinguishing entity types and claim types. The prompt gives the model a schema but no guidance on what constitutes an entity vs. a claim, leading to inconsistent output.

**Finding 3.1b — MEDIUM**: The `entity_name` link in claims is free-text. If the LLM extracts entity "OpenAI" but links a claim to "OpenAI Inc.", the `entity_name_map.get(c.entity_name)` lookup at line 105 silently drops the link. No fuzzy matching, normalization, or alias resolution.

**Finding 3.1c — HIGH**: Entity name deduplication is absent. Running extraction twice on the same source (or similar sources) produces duplicate entities with no deduplication logic. This is a PostgreSQL source-of-truth integrity issue.

**Finding 3.1d — CRITICAL**: Content truncation at `source.raw_content[:8000]` (line 76) is hard-coded with no warning when content exceeds the limit. For a 20,000-character document, 60% of the content is silently discarded. The vector store uses a different truncation (`[:4000]` at line 121) with no justification for the different limits.

**Recommendation**: 
- Add few-shot examples covering all entity types.
- Implement fuzzy name matching for claim→entity linking (e.g., lowercase + strip).
- Add configurable content truncation with warning logs.
- Implement entity deduplication (upsert by name+source_id).

### 3.2 Claim Extraction

**Finding 3.2a — MEDIUM**: The `claim_type` field is free-form with no constrained vocabulary. The prompt offers no guidance on valid claim types, so the LLM may produce inconsistent categorizations (e.g., "factual" vs "fact" vs "statement").

**Finding 3.2b — LOW**: Claims are extracted without context window. The LLM gets a truncated 8000-char chunk and may miss cross-document context needed for accurate claim attribution.

### 3.3 Extraction Log Audit Trail

**File**: `extraction.py` lines 65–149, `schemas.py` lines 217–246

**Finding 3.3a — HIGH**: The extraction log is missing critical audit fields:
- **Model used** (`primary_model` / `fallback_model`): Not recorded — you cannot reproduce extraction results
- **Claims found** count: `update_extraction_log` accepts `entities_found` but has no `claims_found` parameter
- **Latency**: No timing instrumentation
- **Temperature / max_tokens**: Not recorded — reproducibility gap
- **Content length processed**: Not recorded (was it truncated?)
- **Truncation flag**: No indication that content was truncated

Current `ExtractionLogUpdate` schema:
```python
class ExtractionLogUpdate(BaseModel):
    status: Optional[ExtractionStatus] = None
    entities_found: Optional[int] = None      # only entities, no claims
    error_message: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None
```

**Recommendation**: Add `claims_found`, `model_used`, `tokens_used`, `latency_ms`, and `content_truncated` fields to `ExtractionLog` and `ExtractionLogUpdate`.

**Finding 3.3b — LOW**: Vector store population at line 121–129 creates a document with ID `f"source_{source.id}"`. If extraction is re-run on the same source, the ChromaDB `collection.add` with the same ID will upsert (silently overwrite) the existing document — no versioning.

---

## 4. Quality Scoring Audit (`apps/research-agent/research_agent/services/quality.py`)

### 4.1 Quality Pipeline

**Finding 4.1a — MEDIUM**: `LLMQualityResult` (line 17–19) has no Pydantic validators:
```python
class LLMQualityResult(BaseModel):
    score: float         # No Field(ge=0.0, le=1.0) constraint
    reasoning: str
```
An LLM could return `score: 2.5` or `score: -0.1` and it would pass validation. Contrast this with `EntityCreate.confidence` which properly uses `Field(None, ge=0.0, le=1.0)`.

**Finding 4.1b — LOW**: Direct access to `llm_service._primary_model` (line 48) — a private attribute. This works but violates encapsulation. A public `model_name` property would be cleaner.

**Finding 4.1c — LOW**: The threshold `< 0.3` for FAILED is hard-coded and not configurable. Boundary case at exactly 0.3 is well-tested and returns ASSESSED.

### 4.2 Quality Analysis Persistence

**Finding 4.2 — MEDIUM**: The `score_quality()` function creates an `AnalysisCreate` record even if the quality scoring fails mid-pipeline. However, if `generate_structured` raises an exception, the `create_analysis` call is never reached — so failed quality scores are silently lost (no failed Analysis record is created).

**Recommendation**: Wrap in try/except to create a "failed" Analysis record even on LLM errors, similar to how `run_extraction` logs FAILED status.

---

## 5. LLMResponseCache Audit (`packages/northstar-llm/northstar_llm/cache.py`)

### 5.1 Cache Key Design

**Finding 5.1a — PASS**: The cache key includes all determinative parameters:
```python
raw = f"{prompt}|||{model}|||{system_prompt or ''}|||{temperature}|||{max_tokens}"
```
This correctly prevents cache poisoning across models, temperatures, or system prompts. Uses SHA-256 hashing.

**Finding 5.1b — LOW**: `system_prompt` uses `''` when `None`, but the separator `|||` still works. Edge case: a prompt containing `|||` as literal text produces the same hash key as a different prompt with that text legitimately split across parameters. Practically, this collision risk is negligible.

### 5.2 TTL Strategy

**Finding 5.2 — MEDIUM**: Default TTL is 86400s (24 hours), hard-coded and not per-operation. Quality scores and extractions have different freshness requirements — quality scores might benefit from longer caching, while extraction results for rapidly-changing sources might need shorter TTLs.

**Finding 5.3 — LOW**: The `get()` method logs cache hits (`logger.debug("llm_cache_hit")`) but NOT cache misses. This makes it impossible to measure cache effectiveness from logs alone.

**Finding 5.4 — LOW**: `diskcache.Cache` has a default 1GB size limit. For heavy extraction workloads, this could fill up. No size monitoring or eviction logging is present.

**Recommendation**:
- Add `llm_cache_miss` debug logging.
- Consider per-operation TTL (e.g., extraction=1h, quality=24h).
- Add a `cache_stats()` method returning hit/miss counts and size.

---

## 6. Vector Store Audit (`packages/northstar-vector/northstar_vector/client.py`)

### 6.1 Score Normalization

**File**: `client.py` line 184

```python
score = max(0.0, 1.0 - distances[i] / 2.0) if distances else 0.0
```

**Finding 6.1a — MEDIUM**: This normalization assumes **cosine distance** (range [0, 2]). If ChromaDB is configured with a different distance metric (L2, IP), the scores become incorrect:
- **L2 distance**: Range is [0, ∞), so negative scores are possible (clamped to 0.0 by `max()`)
- **Inner Product**: Negative scores for dissimilar items; normalization formula is wrong

The default ChromaDB distance metric is `l2`. Since collection creation at line 43 uses `get_or_create_collection(name="default")` without specifying a `metadata={"hnsw:space": "cosine"}` parameter, the collection likely uses L2 distance, producing incorrect normalized scores.

**Finding 6.1b — CRITICAL**: The `"default"` collection is created at `initialize()` time (line 42–44) without specifying a distance function. On first creation, ChromaDB defaults to L2. But the score normalization formula assumes cosine. This means all search result scores are **semantically wrong** unless the collection was manually created with cosine distance.

**Recommendation**: Explicitly set `metadata={"hnsw:space": "cosine"}` on collection creation, OR dynamically adapt the score normalization formula based on the collection's configured distance metric.

### 6.2 Embedding Integration

**Finding 6.2 — PASS**: The `add_documents()` method correctly handles mixed pre-embedded and non-embedded documents (lines 86–100), using `embed_batch()` for efficient batching. Index alignment is maintained correctly with `docs_without_emb` tracking.

### 6.3 Search Fragility

**Finding 6.3 — LOW**: `search()` does not validate that the query embedding dimension matches the collection's stored dimension. A model swap that changes embedding dimensions produces silent garbage results.

---

## Risk Summary Tables

### Prompt Quality Audit

| Component | Severity | Issue |
|-----------|----------|-------|
| Extraction system prompt | MEDIUM | Zero-shot only; no few-shot examples for entity/claim typing |
| Extraction user prompt | LOW | Template is clear but no content-length warning |
| Quality prompt | LOW | Adequate; single-purpose scoring |
| Claim type vocabulary | MEDIUM | No constrained claim type vocabulary; free-form inconsistent |
| Entity type mapping | LOW | 9 entity types well-defined in `EntityType` enum |

### Error Handling Robustness

| Component | Severity | Issue |
|-----------|----------|-------|
| LLM retry: HTTP errors | **CRITICAL** | 5xx/429 treated as permanent failures; zero retries |
| LLM retry: transport | LOW | 3 retries with 1s/2s backoff (non-standard) |
| EmbeddingService retry | **CRITICAL** | Zero retry logic for any error type |
| JSON parse fallback | MEDIUM | Two strategies; regex fragile for edge cases |
| Extraction error → log | PASS | FAILED status correctly written to audit log |
| Quality error → analysis | MEDIUM | No analysis record created on LLM failure |

### Output Parsing Safety

| Component | Severity | Issue |
|-----------|----------|-------|
| JSON extraction regex | MEDIUM | Non-greedy match can truncate on embedded backticks |
| Pydantic validation | PASS | `model_validate()` catches schema violations |
| `LLMQualityResult.score` | MEDIUM | No `ge=0.0, le=1.0` constraint (unlike confidence fields) |
| Confidence filtering | **HIGH** | Zero-confidence entities/claims persisted; no threshold |
| Hallucination guard | **HIGH** | No source-content anchoring or claim verification |
| Entity deduplication | **HIGH** | Duplicates created on re-extraction; no upsert logic |

### Cache Design Review

| Aspect | Status | Notes |
|--------|--------|-------|
| Key completeness | ✅ PASS | All determinative params included |
| TTL strategy | ⚠️ ADEQUATE | 24h default, not per-operation |
| Hit/miss logging | ⚠️ PARTIAL | Only hits logged; misses invisible |
| Size monitoring | ❌ MISSING | No stats, no eviction visibility |
| Structured output caching | ⚠️ PARTIAL | `generate()` cached; `generate_structured()` re-parses |

---

## Quick Wins (low-effort, high-impact)

1. **Add `Field(ge=0.0, le=1.0)` to `LLMQualityResult.score`** — 1 line, prevents invalid quality scores (quality.py line 18)
2. **Add `claims_found` to extraction log update** — 1 field + 1 line, closes audit gap (schemas.py, extraction.py line 134)
3. **Add cache miss logging** — 1 line in `cache.py` `get()` method
4. **Fix collection creation to use cosine distance** — 1 parameter in `client.py` line 42–44
5. **Add `MIN_CONFIDENCE` threshold filtering** — ~5 lines in extraction pipeline, prevents garbage data

## Structural Issues (require design discussion)

1. **Retry logic redesign** — HTTP errors need retry semantics; currently all 5xx → immediate fallback
2. **EmbeddingService needs retry/error handling parity** with LLMService
3. **Entity deduplication strategy** — upsert by name+source or full dedup pipeline
4. **Extraction log schema expansion** — model, latency, claims_found, truncation flag needed for reproducibility
5. **Hallucination guard architecture** — claim-to-source anchoring, contradiction detection, confidence calibration

---

## Tests to Add

| Test | Priority | Covers |
|------|----------|--------|
| `test_llm_retries_on_http_500` | CRITICAL | Verify 5xx errors are retried (currently untested, and broken) |
| `test_embedding_retry_on_timeout` | CRITICAL | EmbeddingService retry behavior |
| `test_extraction_rejects_low_confidence` | HIGH | Confidence threshold filtering |
| `test_extraction_handles_truncated_content` | MEDIUM | Warning on content > 8000 chars |
| `test_cache_miss_logged` | LOW | Cache miss observability |
| `test_vector_score_normalization_cosine` | MEDIUM | Verify score formula against known cosine distances |
| `test_quality_result_score_clamped` | MEDIUM | Score outside [0,1] rejected |
| `test_extraction_entity_dedup` | HIGH | Duplicate entity detection |
| `test_extraction_log_claims_count` | HIGH | Claims count in extraction log |

---

## Final Risk Level: **MEDIUM**

The pipeline works for happy-path extraction against well-behaved local models, but three issues elevate risk:

1. **CRITICAL**: HTTP errors (5xx, 429) skip retries — every transient Ollama failure cascades to model fallback
2. **CRITICAL**: EmbeddingService has no retry logic — the weakest link breaks vector search silently
3. **HIGH**: No hallucination guards or confidence filtering — LLM output is trusted unconditionally

The cache design, prompt structure, and extraction pipeline flow are fundamentally sound but need hardening around error resilience and output validation.
