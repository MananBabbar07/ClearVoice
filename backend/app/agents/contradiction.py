import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def detect_contradiction(claim: str, papers: list) -> dict:
    context = ""
    for i, paper in enumerate(papers, 1):
        context += f"""
Paper {i}:
Title: {paper['title']}
Journal: {paper['journal']} ({paper['year']})
Abstract: {paper['abstract'][:400]}
Similarity: {paper['similarity']:.2f}
"""

    prompt = f"""You are a medical research analyst. Analyze these studies and determine if they contradict each other regarding the claim.

CLAIM: "{claim}"

STUDIES:
{context}

Analyze the studies and respond in this exact JSON format:
{{
    "has_contradiction": true or false,
    "supporting_papers": [list of paper numbers that support the claim],
    "contradicting_papers": [list of paper numbers that contradict the claim],
    "contradiction_explanation": "one sentence explaining the contradiction if any",
    "suggested_verdict": "TRUE" or "FALSE" or "MISLEADING" or "INSUFFICIENT EVIDENCE"
}}

If some papers support and some contradict → MISLEADING
If all papers support → TRUE
If all papers contradict → FALSE
If papers are unrelated → INSUFFICIENT EVIDENCE

Respond with JSON only."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
    )

    raw = response.choices[0].message.content.strip()

    import json
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {
            "has_contradiction": False,
            "supporting_papers": [],
            "contradicting_papers": [],
            "contradiction_explanation": "Could not analyze contradictions.",
            "suggested_verdict": None
        }


if __name__ == "__main__":
    from retrieval import get_similar_papers
    claim = input("Enter a health claim: ")
    papers = get_similar_papers(claim)
    result = detect_contradiction(claim, papers)
    import json
    print(json.dumps(result, indent=2))