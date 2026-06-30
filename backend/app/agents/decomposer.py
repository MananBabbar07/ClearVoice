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


def decompose_claim(claim: str, retries: int = 3) -> dict:
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
            print(f"Decomposer attempt {attempt+1} failed: {e}")
            time.sleep(2)

    return {
        "is_complex": False,
        "sub_claims": [claim],
        "original_claim": claim
    }


if __name__ == "__main__":
    claim = input("Enter a health claim: ")
    result = decompose_claim(claim)
    print(json.dumps(result, indent=2))