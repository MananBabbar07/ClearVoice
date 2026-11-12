import json
import logging
import os
import re
import string
import sys
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "app"))

import redis
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

load_dotenv(override=True)

from agents.decomposer import decompose_claim
from agents.explainer import explain_verdict
from agents.judge import judge_papers
from retrieval import get_similar_papers
from verify import get_verdict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="ClearVoice API", version="2.0.0")

allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "")
allowed_origins = [origin.strip() for origin in allowed_origins_env.split(",") if origin.strip()]
if not allowed_origins:
    allowed_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


def init_redis_cache():
    redis_url = os.getenv("REDIS_URL")
    if not redis_url:
        logger.warning("[Redis] REDIS_URL not set, running without cache.")
        return None
    try:
        return redis.Redis.from_url(
            redis_url,
            decode_responses=True,
            socket_connect_timeout=3,
            socket_timeout=3,
        )
    except Exception as e:
        logger.warning("[Redis] Failed to initialize client, running without cache: %s", e)
        return None


cache = init_redis_cache()

CACHE_TTL = 60 * 60 * 24


class ClaimRequest(BaseModel):
    claim: str


def normalize_cache_key(claim: str) -> str:
    collapsed = re.sub(r"\s+", " ", claim.strip().lower())
    stripped = collapsed.rstrip(string.punctuation).strip()
    return f"v2:{stripped}"


def safe_float(value, default: float = 0.0) -> float:
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def format_papers(papers: list) -> list:
    return [
        {
            "pmid": p["pmid"],
            "title": p["title"],
            "journal": p["journal"],
            "year": p["year"],
            "similarity": round(float(p["similarity"]), 2),
            "study_type": p.get("study_type", "Other"),
            "publication_types": p.get("publication_types", []),
        }
        for p in papers
    ]


def determine_final_verdict(verdict: dict, judge_result: dict) -> dict:
    papers = judge_result.get("papers") or []
    supports = sum(1 for p in papers if isinstance(p, dict) and p.get("stance") == "SUPPORTS")
    contradicts = sum(1 for p in papers if isinstance(p, dict) and p.get("stance") == "CONTRADICTS")

    if supports > 0 and contradicts > 0:
        verdict["verdict"] = "MISLEADING"
        conf_val = safe_float(verdict.get("confidence"), 0.5)
        verdict["confidence"] = min(conf_val, 0.7)
        verdict["explanation"] = (
            verdict.get("explanation", "")
            + f" Note: Evidence is mixed — {supports} paper(s) support and "
            + f"{contradicts} paper(s) contradict this claim."
        )

    return verdict


def aggregate_sub_results(sub_results: list) -> tuple:
    if len(sub_results) == 1:
        return sub_results[0]["verdict"], sub_results[0]["confidence"], ""

    evidenced = [sr for sr in sub_results if sr["verdict"] != "INSUFFICIENT EVIDENCE"]
    if not evidenced:
        return "INSUFFICIENT EVIDENCE", 0.0, ""

    evidenced_verdicts = [sr["verdict"] for sr in evidenced]
    unverified_claims = [sr["sub_claim"] for sr in sub_results if sr["verdict"] == "INSUFFICIENT EVIDENCE"]

    if all(v == "TRUE" for v in evidenced_verdicts):
        overall_verdict = "TRUE"
    elif all(v == "FALSE" for v in evidenced_verdicts):
        overall_verdict = "FALSE"
    elif all(v == "ERROR" for v in evidenced_verdicts):
        return "ERROR", 0.0, ""
    else:
        overall_verdict = "MISLEADING"

    if unverified_claims:
        evidenced_min_conf = min(sr["confidence"] for sr in evidenced)
        overall_confidence = round(evidenced_min_conf * 0.5, 2)
        note = " Note: Insufficient evidence found for sub-claim(s): " + "; ".join(unverified_claims) + "."
    else:
        overall_confidence = min(sr["confidence"] for sr in sub_results)
        note = ""

    return overall_verdict, overall_confidence, note


@app.get("/")
def root():
    return {"status": "ClearVoice API is running", "version": "2.0.0"}


@app.get("/health")
def health():
    if cache is None:
        return {"status": "ok", "redis": "unavailable"}
    try:
        cache.ping()
        redis_status = "ok"
    except Exception:
        redis_status = "unavailable"
    return {"status": "ok", "redis": redis_status}


@app.post("/verify")
def verify_claim(request: ClaimRequest):
    claim = request.claim.strip()

    if not claim:
        raise HTTPException(status_code=400, detail="Claim cannot be empty")

    cache_key = normalize_cache_key(claim)

    if cache is not None:
        try:
            cached = cache.get(cache_key)
            if cached:
                result = json.loads(cached)
                result["cached"] = True
                return result
        except Exception as e:
            logger.warning("[Redis] Cache read failed, skipping cache: %s", e)

    if " and " in claim.lower() or " or " in claim.lower():
        decomposition = decompose_claim(claim)
    else:
        decomposition = {"is_complex": False, "sub_claims": [claim], "original_claim": claim, "model_used": None}

    decomposer_model = decomposition.pop("model_used", None)
    sub_claims = [sc.strip() for sc in (decomposition.get("sub_claims") or [claim]) if sc and sc.strip()][:3]
    if not sub_claims:
        sub_claims = [claim]
    decomposition["sub_claims"] = sub_claims

    with ThreadPoolExecutor(max_workers=3) as retrieval_executor:
        papers_by_idx = list(retrieval_executor.map(get_similar_papers, sub_claims))

    verdict_futures = {}
    judge_futures = {}
    with ThreadPoolExecutor(max_workers=3) as llm_executor:
        for idx, (sc, sc_papers) in enumerate(zip(sub_claims, papers_by_idx)):
            if sc_papers:
                verdict_futures[idx] = llm_executor.submit(get_verdict, sc, sc_papers)
                judge_futures[idx] = llm_executor.submit(judge_papers, sc, sc_papers)

        verdict_raw_by_idx = {idx: fut.result() for idx, fut in verdict_futures.items()}
        judge_raw_by_idx = {idx: fut.result() for idx, fut in judge_futures.items()}

    sub_results = []
    sub_verdicts_full = []
    sub_judges_full = []
    verdict_models = []
    judge_models = []

    for idx, sc in enumerate(sub_claims):
        sc_papers = papers_by_idx[idx]
        if not sc_papers:
            sc_verdict = {
                "verdict": "INSUFFICIENT EVIDENCE",
                "confidence": 0.0,
                "explanation": "No relevant peer-reviewed studies found for this claim.",
                "citations": [],
            }
            sc_judge = {}
            verdict_model = None
            judge_model = None
        else:
            sc_verdict = determine_final_verdict(verdict_raw_by_idx[idx], judge_raw_by_idx[idx])
            sc_judge = judge_raw_by_idx[idx]
            verdict_model = sc_verdict.pop("model_used", None)
            judge_model = sc_judge.pop("model_used", None)

        formatted_papers = format_papers(sc_papers)
        sub_verdicts_full.append(sc_verdict)
        sub_judges_full.append(sc_judge)
        verdict_models.append(verdict_model)
        judge_models.append(judge_model)
        sub_results.append({
            "sub_claim": sc,
            "verdict": sc_verdict.get("verdict", "ERROR"),
            "confidence": safe_float(sc_verdict.get("confidence"), 0.0),
            "papers": formatted_papers,
        })

    if all(not p for p in papers_by_idx):
        return {
            "verdict": "INSUFFICIENT EVIDENCE",
            "confidence": 0.0,
            "explanation": "No relevant peer-reviewed studies found for this claim.",
            "citations": [],
            "papers": [],
            "judge": {},
            "decomposition": decomposition,
            "sub_results": sub_results,
            "plain_english": "We couldn't find any relevant medical studies to evaluate this claim.",
            "takeaway": "Consult a medical professional for guidance.",
            "evidence_strength": "Insufficient",
            "cached": False,
            "meta": {
                "model_used": {
                    "decomposer": decomposer_model,
                    "verdict": verdict_models,
                    "judge": judge_models,
                    "explainer": None,
                }
            },
        }

    overall_verdict, overall_confidence, unverified_note = aggregate_sub_results(sub_results)

    primary_idx = next((i for i, p in enumerate(papers_by_idx) if p), 0)
    primary_verdict = dict(sub_verdicts_full[primary_idx])
    primary_judge = sub_judges_full[primary_idx]
    primary_papers = sub_results[primary_idx]["papers"]

    if len(sub_results) > 1:
        combined_explanation = " | ".join(
            f"{sr['sub_claim']} -> {sr['verdict']}: {sub_verdicts_full[i].get('explanation', '')}"
            for i, sr in enumerate(sub_results)
        ) + unverified_note
        primary_explanation = combined_explanation
    else:
        combined_explanation = primary_verdict.get("explanation", "")
        primary_explanation = combined_explanation

    explanation_result = explain_verdict(
        claim=claim,
        verdict=overall_verdict,
        confidence=overall_confidence,
        explanation=combined_explanation,
        judge_result=primary_judge,
    )
    explainer_model = explanation_result.pop("model_used", None)

    response_payload = {
        "verdict": overall_verdict,
        "confidence": overall_confidence,
        "explanation": primary_explanation,
        "citations": primary_verdict.get("citations", []),
        "papers": primary_papers,
        "judge": primary_judge,
        "decomposition": decomposition,
        "sub_results": sub_results,
        "plain_english": explanation_result.get("plain_english", ""),
        "takeaway": explanation_result.get("takeaway", ""),
        "evidence_strength": explanation_result.get("evidence_strength", ""),
        "cached": False,
        "meta": {
            "model_used": {
                "decomposer": decomposer_model,
                "verdict": verdict_models,
                "judge": judge_models,
                "explainer": explainer_model,
            }
        },
    }

    if (
        cache is not None
        and all(papers_by_idx)
        and overall_verdict != "ERROR"
        and not any(sr["verdict"] == "ERROR" for sr in sub_results)
    ):
        try:
            cache.setex(cache_key, CACHE_TTL, json.dumps(response_payload))
        except Exception as e:
            logger.warning("[Redis] Cache write failed, skipping cache: %s", e)

    return response_payload
