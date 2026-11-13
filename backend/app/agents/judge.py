import json
import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from groq_client import call_groq
from utils import smart_slice

logger = logging.getLogger(__name__)
JUDGE_MODELS = [
    "openai/gpt-oss-20b",
    "openai/gpt-oss-120b",
]


def extract_json(raw: str) -> dict:
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    try:
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start != -1 and end != 0:
            return json.loads(raw[start:end])
    except json.JSONDecodeError:
        pass
    return None


def _is_valid_judge_response(raw: str, expected: int) -> bool:
    parsed = extract_json(raw)
    if not isinstance(parsed, dict):
        return False
    items = parsed.get("papers")
    if not isinstance(items, list) or len(items) != expected:
        return False
    return all(
        isinstance(p, dict) and str(p.get("stance", "")).upper() in ("SUPPORTS", "CONTRADICTS", "NEUTRAL")
        for p in items
    )


def judge_papers(claim: str, papers: list) -> dict:
    context = ""
    for i, paper in enumerate(papers, 1):
        context += f"""
Paper {i}:
PMID: {paper.get('pmid', '')}
Title: {paper['title']}
Journal: {paper['journal']} ({paper['year']})
Abstract: {smart_slice(paper.get('abstract', ''), 150, 350)}
"""

    prompt = f"""You are a medical research quality assessor. Analyze each study and classify it.

CLAIM: "{claim}"

STUDIES:
{context}

For each paper respond in this exact JSON format:
{{
    "papers": [
        {{
            "paper_number": 1,
            "stance": "SUPPORTS" or "CONTRADICTS" or "NEUTRAL",
            "quality_score": number from 1-5,
            "one_line_summary": "one sentence summary of what this paper found"
        }}
    ],
    "overall_quality": "HIGH" or "MEDIUM" or "LOW",
    "quality_explanation": "one sentence explaining the overall evidence quality"
}}

Respond with JSON only. No extra text, no markdown formatting, no backticks."""

    raw, model_used = call_groq(
        prompt,
        response_format={"type": "json_object"},
        models=JUDGE_MODELS,
        validator=(lambda r: _is_valid_judge_response(r, len(papers))) if papers else None,
    )

    result = extract_json(raw)
    if result is not None and isinstance(result.get("papers"), list):
        enriched_papers = []
        for idx, jp in enumerate(result["papers"]):
            if idx >= len(papers):
                break
            item = jp if isinstance(jp, dict) else {}
            source_paper = papers[idx]
            reported_num = item.get("paper_number")
            if reported_num is not None and reported_num != idx + 1:
                logger.warning("Judge paper_number %s != expected position %d", reported_num, idx + 1)
            item["paper_number"] = idx + 1
            item["pmid"] = source_paper.get("pmid", "")
            item["study_type"] = source_paper.get("study_type", "Other")
            stance = str(item.get("stance", "NEUTRAL")).upper()
            item["stance"] = stance if stance in ("SUPPORTS", "CONTRADICTS", "NEUTRAL") else "NEUTRAL"
            enriched_papers.append(item)
        result["papers"] = enriched_papers
        result["model_used"] = model_used
        return result

    return {
        "papers": [],
        "overall_quality": "UNKNOWN",
        "quality_explanation": "Could not assess study quality.",
        "model_used": model_used,
    }


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from retrieval import get_similar_papers
    claim = input("Enter a health claim: ")
    papers = get_similar_papers(claim)
    result = judge_papers(claim, papers)
    print(json.dumps(result, indent=2))
