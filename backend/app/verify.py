
import os
import json
from dotenv import load_dotenv
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


def build_prompt(claim: str, papers: list) -> str:
    context = ""
    for i, paper in enumerate(papers, 1):
        context += f"""
Paper {i}:
PMID: {paper['pmid']}
Title: {paper['title']}
Journal: {paper['journal']} ({paper['year']})
Abstract: {paper['abstract'][:500]}
Similarity: {paper['similarity']:.2f}
"""

    prompt = f"""You are a medical fact-checker. A user has submitted a health claim.
You have been given {len(papers)} relevant peer-reviewed studies from PubMed.

USER CLAIM: "{claim}"

RELEVANT STUDIES:
{context}

IMPORTANT: Use only the exact PMIDs provided in the studies above for citations.
Do not use "not available" or "not provided" — only cite papers with real PMIDs from the list above.

Based on these studies, evaluate the claim and respond in this exact JSON format:
{{
    "verdict": "TRUE" or "FALSE" or "MISLEADING" or "INSUFFICIENT EVIDENCE",
    "confidence": a number between 0.0 and 1.0,
    "explanation": "2-3 sentence explanation of your verdict",
    "citations": [
        {{
            "pmid": "the exact pmid from the studies above",
            "title": "the title",
            "relevance": "one sentence on why this paper is relevant"
        }}
    ]
}}

Respond with JSON only. No extra text, no markdown formatting, no backticks."""

    return prompt


def get_verdict(claim: str, papers: list) -> dict:
    prompt = build_prompt(claim, papers)
    raw = call_groq(prompt)

    result = extract_json(raw)
    if result is not None:
        return result

    return {
        "verdict": "ERROR",
        "confidence": 0.0,
        "explanation": "Failed to parse LLM response.",
        "citations": []
    }


if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from retrieval import get_similar_papers

    claim = input("Enter a health claim: ")
    papers = get_similar_papers(claim)
    verdict = get_verdict(claim, papers)
    print(json.dumps(verdict, indent=2))