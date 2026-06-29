import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

STUDY_QUALITY = {
    "meta-analysis": 5,
    "systematic review": 5,
    "rct": 5,
    "randomized controlled trial": 5,
    "cohort": 3,
    "case-control": 3,
    "cross-sectional": 2,
    "case report": 1,
    "case study": 1,
    "opinion": 1,
    "review": 2,
    "unknown": 1
}


def judge_papers(claim: str, papers: list) -> dict:
    context = ""
    for i, paper in enumerate(papers, 1):
        context += f"""
Paper {i}:
Title: {paper['title']}
Journal: {paper['journal']} ({paper['year']})
Abstract: {paper['abstract'][:400]}
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

Respond with JSON only."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
    )

    raw = response.choices[0].message.content.strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {
            "papers": [],
            "overall_quality": "UNKNOWN",
            "quality_explanation": "Could not assess study quality."
        }


if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from retrieval import get_similar_papers
    claim = input("Enter a health claim: ")
    papers = get_similar_papers(claim)
    result = judge_papers(claim, papers)
    print(json.dumps(result, indent=2))