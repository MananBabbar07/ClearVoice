import os
import json
import time
from groq import Groq
from dotenv import load_dotenv

load_dotenv(override=True)

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def extract_json(raw: str) -> dict:
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


def explain_verdict(claim: str, verdict: str, confidence: float, explanation: str, judge_result: dict, retries: int = 3) -> dict:
    overall_quality = judge_result.get("overall_quality", "UNKNOWN")
    quality_explanation = judge_result.get("quality_explanation", "")

    prompt = f"""You are a medical communicator who explains complex medical verdicts in plain English for everyday people.

CLAIM: "{claim}"
VERDICT: {verdict}
CONFIDENCE: {confidence * 100:.0f}%
TECHNICAL EXPLANATION: {explanation}
EVIDENCE QUALITY: {overall_quality}
QUALITY NOTE: {quality_explanation}

Write a plain English summary that:
1. States the verdict clearly in simple words
2. Explains WHY in 1-2 sentences a non-doctor would understand
3. Mentions how strong the evidence is
4. Adds a practical takeaway if relevant

Respond in this exact JSON format:
{{
    "plain_english": "2-3 sentence plain English summary",
    "takeaway": "one practical takeaway for the user",
    "evidence_strength": "Strong" or "Moderate" or "Weak" or "Insufficient"
}}

Respond with JSON only. No extra text, no markdown formatting, no backticks."""

    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
            )

            raw = response.choices[0].message.content.strip()
            raw = raw.replace("```json", "").replace("```", "").strip()

            result = extract_json(raw)
            if result is not None:
                return result

        except Exception as e:
            print(f"Explainer attempt {attempt+1} failed: {e}")
            time.sleep(2)

    return {
        "plain_english": explanation,
        "takeaway": "",
        "evidence_strength": "Unknown"
    }


if __name__ == "__main__":
    result = explain_verdict(
        claim="vaccines cause autism",
        verdict="FALSE",
        confidence=0.9,
        explanation="No peer-reviewed evidence supports a link between vaccines and autism.",
        judge_result={"overall_quality": "HIGH", "quality_explanation": "Multiple RCTs found."}
    )
    print(json.dumps(result, indent=2))