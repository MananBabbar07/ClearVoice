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

## Cold vs Warm Latency Protocol

> [!IMPORTANT]
> **Flush the Redis cache before every cold-latency benchmark run** (e.g., `redis-cli -u "$REDIS_URL" FLUSHDB` or `python clear_cache.py`). Otherwise cached `v2:` keys will return warm cache hits and underreport cold retrieval + LLM latency.

To measure warm latency, run `python benchmark.py` a second time immediately after a cold run without flushing Redis.

### Cold vs Warm

| Metric | Cold Run (Cache Flushed) | Warm Run (Cache Hit) |
|--------|--------------------------|----------------------|
| Total Claims | 50 | 50 |
| Overall Accuracy | TBD | TBD |
| Avg Latency (s) | TBD | TBD |
| p50 Latency (s) | TBD | TBD |
| p95 Latency (s) | TBD | TBD |
| Errors | TBD | TBD |

## PUBHEALTH Benchmark Evaluation

### Overview & Citation
PUBHEALTH is a comprehensive dataset for explainable automated fact-checking of public health claims:

> Kotonya, N., & Toni, F. (2020). *Explainable Automated Fact-Checking for Public Health Claims*. In Proceedings of the 2020 Conference on Empirical Methods in Natural Language Processing (EMNLP), pages 7740–7754.

The dataset contains claims verified by journalistic fact-checking organizations with veracity labels and explanatory reviews.

### Label Mapping
PUBHEALTH test split labels map to ClearVoice verdicts as follows:

| PUBHEALTH Original Label | ClearVoice Expected Verdict | Category |
|--------------------------|-----------------------------|----------|
| `true` | `TRUE` | `true` |
| `false` | `FALSE` | `false` |
| `mixture` | `MISLEADING` | `misleading` |
| `unproven` | `INSUFFICIENT EVIDENCE` | `insufficient` |

Rows with label `-1` (unlabelled / invalid) are discarded.

### Filtering Rules & Sampling Protocol
- **Claim length**: Strictly under 200 characters (`< 200`).
- **Non-empty**: Empty or whitespace-only claims dropped.
- **Normalization**: Leading and trailing whitespace trimmed.
- **De-duplication**: Exact case-insensitive duplicate claims dropped.
- **Label filtering**: Rows with label `-1` dropped.
- **Stratified sampling**: 14 claims sampled per class using fixed random seed `42` (`random.Random(42)`), yielding 56 total benchmark claims written to `benchmark_pubhealth.json`.

### Caveats
1. **Fact-checker ground truth vs. PubMed consensus**: PUBHEALTH labels originate from journalistic fact-checkers (e.g. Snopes, FactCheck.org, PolitiFact) evaluating media claims and public statements, rather than systematic biomedical literature reviews.
2. **"Unproven" vs. "Insufficient Evidence"**: Journalistic "unproven" often means a specific claim lacks official confirmation or proof at the time of fact-checking, which does not always strictly correlate with zero scientific studies existing on PubMed.
3. **Dynamic retrieval**: ClearVoice queries PubMed live in real time; results reflect the state of PubMed indexed literature on the date of execution.
4. **Prevalence of non-medical claims**: A notable fraction of PUBHEALTH claims represent social media hoaxes, political news, or urban legends with no biomedical literature indexed in PubMed. For example:
   - *"A trojan worm known as Koobface is 'spreading like wildfire' via Facebook."* (malware warning)
   - *"A viral warning claims that a drug called burundanga on a business card poisoned a woman and advises people to beware of what has become known as 'the zombie drug.'"* (urban legend)
   - *"Judge considers Hammond Ranches grazing permit."* (legal/land-use dispute)
   - *"After passing a bill to make consuming raw milk legal in the state, several members of the West Virginia legislature fell ill due to drinking raw milk to celebrate the bill becoming law."* (political news)
   - *"A Twitter user responded to Stephen King's assertion the COVID-19 pandemic was 'not like The Stand,' sincerely asking King if he 'even read' a book he actually wrote."* (celebrity social media exchange)

Because ClearVoice is specifically designed to verify biomedical claims against peer-reviewed PubMed literature, evaluating on a dedicated biomedical benchmark (SciFact) provides direct measurement of scientific evidence reasoning.

### Results

#### Overall Performance

| Metric | Value |
|--------|-------|
| Benchmark File | `benchmark_pubhealth.json` |
| Total Claims | 56 |
| Correct | TBD |
| Errors | TBD |
| Overall Accuracy | TBD |
| Cold Latency (Avg) | TBD |
| Cold Latency (p50) | TBD |
| Cold Latency (p95) | TBD |

#### Per-Class Accuracy

| Class | Total | Correct | Accuracy |
|-------|-------|---------|----------|
| `true` | 14 | TBD | TBD |
| `false` | 14 | TBD | TBD |
| `misleading` | 14 | TBD | TBD |
| `insufficient` | 14 | TBD | TBD |

#### Confusion Matrix

| Expected \ Predicted | TRUE | FALSE | MISLEADING | INSUFFICIENT EVIDENCE | ERROR |
|----------------------|------|-------|------------|-----------------------|-------|
| **TRUE** | TBD | TBD | TBD | TBD | TBD |
| **FALSE** | TBD | TBD | TBD | TBD | TBD |
| **MISLEADING** | TBD | TBD | TBD | TBD | TBD |
| **INSUFFICIENT EVIDENCE** | TBD | TBD | TBD | TBD | TBD |

## SciFact Benchmark Evaluation

### Overview & Citation
SciFact is a benchmark dataset for verifying scientific claims against research abstracts:

> Wadden, D., Lin, S., Lo, K., Wang, L. L., van Zuylen, M., Cohan, A., & Hajishirzi, H. (2020). *Fact or Fiction: Verifying Scientific Claims with Evidence*. In Proceedings of the 2020 Conference on Empirical Methods in Natural Language Processing (EMNLP), pages 8134–8146.

Claims in SciFact are generated by scientific domain experts and paired with peer-reviewed biomedical abstracts from PubMed and PMC.

### Split & Label Mapping
ClearVoice evaluates on the **validation split** of the `claims` config (the test split does not include publicly accessible ground truth labels). The label mapping is:

| SciFact Evidence Label | ClearVoice Expected Verdict | Category |
|-----------------------|-----------------------------|----------|
| `SUPPORT` | `TRUE` | `true` |
| `CONTRADICT` | `FALSE` | `false` |
| No evidence (empty / NEI) | `INSUFFICIENT EVIDENCE` | `insufficient` |

### Filtering Rules & Sampling Protocol
- **Claim length**: Strictly under 200 characters (`< 200`).
- **Deduplication**: Case-insensitive deduplication across claims.
- **Conflicting evidence resolution**: Claims with multiple contradictory evidence citations (both `SUPPORT` and `CONTRADICT` in the same split) are discarded.
- **Stratified sampling**: 20 claims sampled per class using fixed random seed `42` (`random.Random(42)`), producing 60 total benchmark claims written to `benchmark_scifact.json`.

### Caveats
1. **Absence of a MISLEADING category**: SciFact is structured around 3-way classification (`SUPPORT`, `CONTRADICT`, `NOT ENOUGH INFO`). It does not annotate mixed or nuanced claims as `MISLEADING`, a category ClearVoice identifies through its Judge agent when evidence is divided.
2. **Abstract-level scope**: SciFact ground-truth evidence is scoped to specific cited abstract sentences, whereas ClearVoice performs live retrieval across all of PubMed to ground verdicts in the broader medical literature.

### Results

#### Overall Performance

| Metric | Value |
|--------|-------|
| Benchmark File | `benchmark_scifact.json` |
| Total Claims | 60 |
| Correct | TBD |
| Errors | TBD |
| Overall Accuracy | TBD |
| Cold Latency (Avg) | TBD |
| Cold Latency (p50) | TBD |
| Cold Latency (p95) | TBD |

#### Per-Class Accuracy

| Class | Total | Correct | Accuracy |
|-------|-------|---------|----------|
| `true` | 20 | TBD | TBD |
| `false` | 20 | TBD | TBD |
| `insufficient` | 20 | TBD | TBD |

#### Confusion Matrix

| Expected \ Predicted | TRUE | FALSE | MISLEADING | INSUFFICIENT EVIDENCE | ERROR |
|----------------------|------|-------|------------|-----------------------|-------|
| **TRUE** | TBD | TBD | TBD | TBD | TBD |
| **FALSE** | TBD | TBD | TBD | TBD | TBD |
| **INSUFFICIENT EVIDENCE** | TBD | TBD | TBD | TBD | TBD |

