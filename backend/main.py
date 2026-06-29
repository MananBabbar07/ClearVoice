import sys
import os
import json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "app"))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import redis

load_dotenv()

from retrieval import get_similar_papers
from verify import get_verdict

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

    papers = get_similar_papers(claim)

    if not papers:
        raise HTTPException(status_code=404, detail="No relevant papers found")

    verdict = get_verdict(claim, papers)

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
    verdict["cached"] = False

    cache.setex(claim, CACHE_TTL, json.dumps(verdict))

    return verdict