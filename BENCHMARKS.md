# ClearVoice Benchmarks

## Overview

| Metric | Value |
|--------|-------|
| Total papers ingested | 12,887 |
| Search topics | 27 |
| Embedding model | all-MiniLM-L6-v2 (384d) |
| LLM | Groq llama-3.3-70b-versatile |
| Database | Supabase (pgvector, IVFFlat lists=200) |
| Cache | Upstash Redis (24hr TTL) |

## Performance History

| Metric | Phase 1 v1 | Phase 1 v2 | Phase 2 Target |
|--------|-----------|-----------|----------------|
| Papers in DB | 3,735 | 12,887 | 15,000+ |
| Search topics | 8 | 27 | 30+ |
| Accuracy | 60% | 80% | 90%+ |
| Avg confidence | 0.69 | 0.88 | 0.90+ |
| Avg top similarity | 0.45 | 0.61 | 0.75+ |
| Avg response time | 4.19s | 6.21s | <5s |
| Cache hit response | <100ms | <100ms | <100ms |
| MISLEADING accuracy | 0% | 50% | 85%+ |
| Embedding model | MiniLM | MiniLM | BioBERT |

## Verdict Breakdown (Phase 1 v2)

| Verdict | Count |
|---------|-------|
| FALSE | 3 |
| TRUE | 4 |
| MISLEADING | 2 |
| ERROR | 1 |

## Failure Analysis

| Claim | Expected | Got | Reason |
|-------|----------|-----|--------|
| sugar causes diabetes | MISLEADING | ERROR | Groq rate limit |
| stress causes high blood pressure | MISLEADING | TRUE | No contradiction detection |

## Phase 2 Improvements Planned
- BioBERT embeddings for better medical retrieval
- Contradiction agent for MISLEADING detection
- Judge agent to weigh study quality
- Decomposer agent for complex claims
- Explainer agent for plain English summaries
- Corpus expansion to 15,000+ papers