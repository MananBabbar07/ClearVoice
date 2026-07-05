import os
import time
from groq import Groq

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

MODELS = [
    "llama-3.3-70b-versatile",
    "meta-llama/llama-4-scout-17b-16e-instruct",
    "openai/gpt-oss-120b",
    "llama-3.1-8b-instant",
]


def call_groq(prompt: str, retries: int = 2) -> str:
    for model in MODELS:
        for attempt in range(retries):
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                )
                raw = response.choices[0].message.content.strip()
                raw = raw.replace("```json", "").replace("```", "").strip()
                print(f"✅ Used model: {model}")
                return raw
            except Exception as e:
                error_str = str(e)
                if "rate_limit" in error_str.lower() or "429" in error_str:
                    print(f"⚠️ {model} rate limited, trying next...")
                    break
                elif "401" in error_str:
                    print(f"❌ {model} auth error: {e}")
                    break
                else:
                    print(f"⚠️ {model} attempt {attempt+1} failed: {e}")
                    time.sleep(2)

    return None