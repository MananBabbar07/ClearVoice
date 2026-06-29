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

| Metric | Phase 1 v1 | Phase 1 v2 | Phase 2 | Phase 2 + Judge |
|--------|-----------|-----------|---------|-----------------|
| Papers in DB | 3,735 | 12,887 | 12,887 | 12,887 |
| Search topics | 8 | 27 | 27 | 27 |
| Embedding model | MiniLM | MiniLM | PubMedBERT | PubMedBERT |
| Accuracy | 60% | 80% | 90%+ | 90% |
| Avg confidence | 0.69 | 0.88 | 0.84 | 0.85 |
| Avg top similarity | 0.45 | 0.61 | 0.54 | 0.54 |
| Avg response time | 4.19s | 6.21s | 9.16s | 7.72s |
| Cache hit response | <100ms | <100ms | <100ms | <100ms |
| MISLEADING accuracy | 0% | 50% | 100% | 67% |
| Errors | 2 | 1 | 0 | 0 |

## Verdict Breakdown (Phase 2 + Judge)

| Verdict | Count |
|---------|-------|
| FALSE | 3 |
| TRUE | 4 |
| MISLEADING | 2 |
| ERROR | 0 |

## Failure Analysis

| Claim | Expected | Got | Reason |
|-------|----------|-----|--------|
| stress causes high blood pressure | MISLEADING | TRUE | Insufficient contradicting papers in DB |

## Key Improvements
- Corpus expanded 3,735 → 12,887 papers (+245%)
- MiniLM → PubMedBERT embeddings (768d, medical-optimized)
- Judge agent added — classifies study type, stance, quality score
- Parallel execution of verdict + judge (ThreadPoolExecutor)
- Response time improved 9.16s → 7.72s with parallel calls
- Zero errors across all benchmark runs

## Phase 3 Targets
| Metric | Phase 2 | Phase 3 Target |
|--------|---------|----------------|
| Accuracy | 90% | 95%+ |
| Test set size | 10 claims | 50+ claims |
| Avg response time | 7.72s | <5s |
| Papers in DB | 12,887 | 20,000+ |
| Frontend | Streamlit | React + Vercel |
| Voice input | No | Whisper API |
| Browser extension | No | Chrome/Edge |