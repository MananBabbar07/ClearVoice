import os
import json
from dotenv import load_dotenv
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from groq_client import call_groq

load_dotenv(override=True)


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


def decompose_claim(claim: str) -> dict:
    prompt = f"""You are a medical claim analyzer. Break down the following health claim into simple sub-claims if it contains multiple assertions.

CLAIM: "{claim}"

Respond in this exact JSON format:
{{
    "is_complex": true or false,
    "sub_claims": ["sub-claim 1", "sub-claim 2"],
    "original_claim": "{claim}"
}}

Rules:
- If claim is simple (one assertion) → is_complex: false, sub_claims contains only the original claim
- If claim has multiple assertions → is_complex: true, break into individual sub-claims
- Maximum 4 sub-claims

Respond with JSON only. No extra text, no markdown formatting, no backticks."""

    raw = call_groq(prompt)
    result = extract_json(raw)
    if result is not None:
        return result

    return {
        "is_complex": False,
        "sub_claims": [claim],
        "original_claim": claim
    }


if __name__ == "__main__":
    claim = input("Enter a health claim: ")
    result = decompose_claim(claim)
    print(json.dumps(result, indent=2))