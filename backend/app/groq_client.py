import os
import time
import logging
from groq import Groq

logger = logging.getLogger(__name__)
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

MODELS = [
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
]


def call_groq(prompt: str, retries: int = 2, response_format: dict = None, models: list = None, validator=None):
    model_list = models if models is not None else MODELS
    for model in model_list:
        for attempt in range(retries):
            try:
                kwargs = {
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.1,
                }
                if response_format:
                    kwargs["response_format"] = response_format

                response = client.chat.completions.create(**kwargs)
                raw = response.choices[0].message.content.strip()
                raw = raw.replace("```json", "").replace("```", "").strip()
                if validator is not None and not validator(raw):
                    logger.warning("[Validation] %s attempt %d failed validation", model, attempt + 1)
                    continue
                logger.info("[OK] Used model: %s", model)
                return raw, model
            except Exception as e:
                error_str = str(e)
                if "rate_limit" in error_str.lower() or "429" in error_str:
                    logger.warning("[RateLimit] %s rate limited, trying next...", model)
                    break
                elif "401" in error_str:
                    logger.warning("[AuthError] %s auth error: %s", model, e)
                    break
                elif "404" in error_str or "model_not_found" in error_str.lower():
                    logger.warning("[ModelNotFound] %s unavailable: %s", model, e)
                    break
                else:
                    logger.warning("[Error] %s attempt %d failed: %s", model, attempt + 1, e)
                    time.sleep(2)

    return None, None