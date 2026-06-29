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

| Metric | Phase 1 v1 | Phase 1 v2 | Phase 2 |
|--------|-----------|-----------|---------|
| Papers in DB | 3,735 | 12,887 | 12,887 |
| Search topics | 8 | 27 | 27 |
| Embedding model | MiniLM | MiniLM | PubMedBERT |
| Accuracy | 60% | 80% | 90%+ |
| Avg confidence | 0.69 | 0.88 | 0.84 |
| Avg top similarity | 0.45 | 0.61 | 0.54 |
| Avg response time | 4.19s | 6.21s | 9.16s |
| Cache hit response | <100ms | <100ms | <100ms |
| MISLEADING accuracy | 0% | 50% | 100% |
| Errors | 2 | 1 | 0 |

## Verdict Breakdown (Phase 2 Final)

| Verdict | Count |
|---------|-------|
| FALSE | 3 |
| TRUE | 4 |
| MISLEADING | 3 |
| ERROR | 0 |

## Failure Analysis

| Claim | Expected | Got | Reason |
|-------|----------|-----|--------|
| None | — | — | All claims correctly classified |

## Key Improvements Phase 1 → Phase 2
- Corpus expanded from 3,735 → 12,887 papers (+245%)
- Embedding model upgraded MiniLM → PubMedBERT (768d)
- MISLEADING detection improved from 0% → 100%
- Zero errors on benchmark test set
- 27 medical topics covered vs 8 in Phase 1

## Phase 3 Targets
| Metric | Phase 2 | Phase 3 Target |
|--------|---------|----------------|
| Accuracy | 90%+ | 95%+ on expanded test set |
| Test set size | 10 claims | 50+ claims |
| Avg response time | 9.16s | <5s |
| Papers in DB | 12,887 | 20,000+ |
| MISLEADING accuracy | 100% | Validated on larger set |
| Judge agent | No | Yes |
| Decomposer agent | No | Yes |