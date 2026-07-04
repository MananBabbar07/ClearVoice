import sys
import os
import json
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "app"))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import redis

load_dotenv()

from retrieval import get_similar_papers
from verify import get_verdict
from agents.judge import judge_papers
from agents.decomposer import decompose_claim
from agents.explainer import explain_verdict

app = FastAPI(title="ClearVoice API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

cache = redis.Redis.from_url(os.getenv("REDIS_URL"), decode_responses=True)

CACHE_TTL = 60 * 60 * 24


class ClaimRequest(BaseModel):
    claim: str


def determine_final_verdict(verdict: dict, judge_result: dict) -> dict:
    papers = judge_result.get("papers", [])
    supports = sum(1 for p in papers if p.get("stance") == "SUPPORTS")
    contradicts = sum(1 for p in papers if p.get("stance") == "CONTRADICTS")

    if supports > 0 and contradicts > 0:
        verdict["verdict"] = "MISLEADING"
        verdict["confidence"] = min(verdict.get("confidence", 0.5), 0.7)
        verdict["explanation"] = verdict.get("explanation", "") + f" Note: Evidence is mixed — {supports} paper(s) support and {contradicts} paper(s) contradict this claim."

    return verdict


@app.get("/")
def root():
    return {"status": "ClearVoice API is running", "version": "2.0.0"}


@app.get("/health")
def health():
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

    cached = cache.get(claim)
    if cached:
        result = json.loads(cached)
        result["cached"] = True
        return result

    if " and " in claim.lower() or " or " in claim.lower():
        decomposition = decompose_claim(claim)
    else:
        decomposition = {"is_complex": False, "sub_claims": [claim], "original_claim": claim}

    primary_claim = decomposition["sub_claims"][0]

    papers = get_similar_papers(primary_claim)

    if not papers:
        return {
            "verdict": "INSUFFICIENT EVIDENCE",
            "confidence": 0.0,
            "explanation": "No relevant peer-reviewed studies found for this claim.",
            "citations": [],
            "papers": [],
            "judge": {},
            "decomposition": decomposition,
            "plain_english": "We couldn't find any relevant medical studies to evaluate this claim.",
            "takeaway": "Consult a medical professional for guidance.",
            "evidence_strength": "Insufficient",
            "cached": False
        }

    with ThreadPoolExecutor(max_workers=2) as executor:
        verdict_future = executor.submit(get_verdict, primary_claim, papers)
        judge_future = executor.submit(judge_papers, primary_claim, papers)

        verdict = verdict_future.result()
        judge_result = judge_future.result()

    verdict = determine_final_verdict(verdict, judge_result)

    explanation_result = explain_verdict(
        claim=claim,
        verdict=verdict.get("verdict", ""),
        confidence=verdict.get("confidence", 0),
        explanation=verdict.get("explanation", ""),
        judge_result=judge_result
    )

    verdict["papers"] = [
        {
            "pmid": p["pmid"],
            "title": p["title"],
            "journal": p["journal"],
            "year": p["year"],
            "similarity": round(float(p["similarity"]), 2)
        }
        for p in papers
    ]
    verdict["judge"] = judge_result
    verdict["decomposition"] = decomposition
    verdict["plain_english"] = explanation_result.get("plain_english", "")
    verdict["takeaway"] = explanation_result.get("takeaway", "")
    verdict["evidence_strength"] = explanation_result.get("evidence_strength", "")
    verdict["cached"] = False

    cache.setex(claim, CACHE_TTL, json.dumps(verdict))

    return verdict