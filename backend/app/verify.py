import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv(dotenv_path="E:/ClearVoice/.env", override=True)

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def build_prompt(claim: str, papers: list) -> str:
    context = ""
    for i, paper in enumerate(papers, 1):
        context += f"""
Paper {i}:
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

Based on these studies, evaluate the claim and respond in this exact JSON format:
{{
    "verdict": "TRUE" or "FALSE" or "MISLEADING" or "INSUFFICIENT EVIDENCE",
    "confidence": a number between 0.0 and 1.0,
    "explanation": "2-3 sentence explanation of your verdict",
    "citations": [
        {{
            "pmid": "the pmid",
            "title": "the title",
            "relevance": "one sentence on why this paper is relevant"
        }}
    ]
}}

Respond with JSON only. No extra text."""

    return prompt


def get_verdict(claim: str, papers: list) -> dict:
    prompt = build_prompt(claim, papers)

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
            "verdict": "ERROR",
            "confidence": 0.0,
            "explanation": "Failed to parse LLM response.",
            "citations": []
        }


if __name__ == "__main__":
    from retrieval import get_similar_papers

    claim = input("Enter a health claim: ")
    papers = get_similar_papers(claim)
    verdict = get_verdict(claim, papers)

    import json
    print(json.dumps(verdict, indent=2))