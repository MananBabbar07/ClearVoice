# ClearVoice Benchmarks

## Overview

| Metric | Value |
|--------|-------|
| Total papers ingested | 12,887 |
| Search topics | 27 |
| Embedding model | NeuML/pubmedbert-base-embeddings (768d) |
| LLM | Groq llama-3.3-70b-versatile |
| Database | Supabase (pgvector, IVFFlat lists=50) |
| Cache | Upstash Redis (24hr TTL) |

## Performance History

| Metric | Phase 1 v1 | Phase 1 v2 | Phase 2 (BioBERT) |
|--------|-----------|-----------|------------------|
| Papers in DB | 3,735 | 12,887 | 12,887 |
| Search topics | 8 | 27 | 27 |
| Embedding model | MiniLM | MiniLM | PubMedBERT |
| Accuracy | 60% | 80% | 90% |
| Avg confidence | 0.69 | 0.88 | 0.87 |
| Avg top similarity | 0.45 | 0.61 | 0.61 |
| Avg response time | 4.19s | 6.21s | 3.86s |
| Cache hit response | <100ms | <100ms | <100ms |
| MISLEADING accuracy | 0% | 50% | 75% |

## Verdict Breakdown (Phase 2)

| Verdict | Count |
|---------|-------|
| FALSE | 3 |
| TRUE | 4 |
| MISLEADING | 2 |
| ERROR | 0 |

## Failure Analysis

| Claim | Expected | Got | Reason |
|-------|----------|-----|--------|
| stress causes high blood pressure | MISLEADING | TRUE | Needs contradiction agent |

## Phase 2 Remaining
- Contradiction agent — detect conflicting studies
- Judge agent — weigh study quality
- Decomposer agent — break complex claims
- Explainer agent — plain English summaries

## Phase 3 Targets
| Metric | Phase 2 | Phase 3 Target |
|--------|---------|----------------|
| Accuracy | 90% | 95%+ |
| Avg top similarity | 0.61 | 0.75+ |
| Avg response time | 3.86s | <3s |
| MISLEADING accuracy | 75% | 90%+ |