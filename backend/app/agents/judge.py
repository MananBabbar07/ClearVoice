import os
import json
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from groq_client import call_groq


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


def judge_papers(claim: str, papers: list) -> dict:
    context = ""
    for i, paper in enumerate(papers, 1):
        context += f"""
Paper {i}:
Title: {paper['title']}
Journal: {paper['journal']} ({paper['year']})
Abstract: {paper['abstract'][:200]}
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
            "study_type": "RCT" or "Meta-Analysis" or "Systematic Review" or "Cohort" or "Case-Control" or "Cross-Sectional" or "Case Report" or "Review" or "Opinion" or "Unknown",
            "stance": "SUPPORTS" or "CONTRADICTS" or "NEUTRAL",
            "quality_score": number from 1-5,
            "one_line_summary": "one sentence summary of what this paper found"
        }}
    ],
    "overall_quality": "HIGH" or "MEDIUM" or "LOW",
    "quality_explanation": "one sentence explaining the overall evidence quality"
}}

Respond with JSON only. No extra text, no markdown formatting, no backticks."""

    raw = call_groq(prompt)
    print(f"Judge raw response: {raw[:300] if raw else 'None'}")

    result = extract_json(raw)
    if result is not None:
        return result

    return {
        "papers": [],
        "overall_quality": "UNKNOWN",
        "quality_explanation": "Could not assess study quality."
    }


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from retrieval import get_similar_papers
    claim = input("Enter a health claim: ")
    papers = get_similar_papers(claim)
    result = judge_papers(claim, papers)
    print(json.dumps(result, indent=2))