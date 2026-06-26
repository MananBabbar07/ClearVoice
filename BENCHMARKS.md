# ClearVoice Benchmarks

## Phase 1 Baseline

| Metric | Value |
|--------|-------|
| Total papers ingested | 3,735 |
| Search topics | 8 |
| Embedding model | all-MiniLM-L6-v2 (384d) |
| LLM | Groq llama-3.3-70b-versatile |
| Database | Supabase (pgvector) |
| Cache | Upstash Redis (24hr TTL) |

### Performance (10 claim test set)
| Metric | Phase 1 |
|--------|---------|
| Accuracy | 60% (6/10) |
| Avg confidence | 0.69 |
| Avg top similarity | 0.45 |
| Avg response time | 4.19s |
| Cache hit response | <100ms |

### Verdict Breakdown
| Verdict | Count |
|---------|-------|
| FALSE | 3 |
| TRUE | 4 |
| INSUFFICIENT EVIDENCE | 3 |
| MISLEADING | 0 |

### Failure Analysis
| Claim | Expected | Got | Reason |
|-------|----------|-----|--------|
| smoking causes lung cancer | TRUE | INSUFFICIENT EVIDENCE | No smoking papers in DB |
| vitamin C prevents colds | MISLEADING | INSUFFICIENT EVIDENCE | Low similarity (0.32), wrong papers |
| sugar causes diabetes | MISLEADING | INSUFFICIENT EVIDENCE | Papers not specific enough |
| stress causes high blood pressure | MISLEADING | TRUE | No contradicting papers retrieved |

### Key Weaknesses
- MISLEADING verdict never triggered — needs contradiction detection
- Low similarity scores (avg 0.45) — MiniLM not optimized for medical text
- Missing search terms for smoking, vitamin C colds, sugar/insulin

## Phase 2 Targets
| Metric | Phase 1 | Phase 2 Target |
|--------|---------|----------------|
| Accuracy | 60% | 85%+ |
| Avg top similarity | 0.45 | 0.65+ |
| Avg response time | 4.19s | <4s |
| Papers in DB | 3,735 | 10,000+ |
| Embedding model | MiniLM | BioBERT |
| MISLEADING accuracy | 0% | 70%+ |

## Phase 2 Planned Improvements
- BioBERT embeddings for better medical text retrieval
- Contradiction agent to detect conflicting studies
- Judge agent to weigh study quality (RCT > cohort > case study)
- Decomposer agent for complex multi-part claims
- Expanded corpus with 20+ search terms