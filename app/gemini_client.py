"""Thin wrapper around the google-genai SDK with model fallback."""
import logging
from functools import lru_cache

from app import config

log = logging.getLogger("fitbuddy.gemini")


class GeminiUnavailable(Exception):
    """Raised when Gemini cannot be used (no key, network error, quota, ...)."""


def is_configured() -> bool:
    return bool(config.GEMINI_API_KEY)


@lru_cache(maxsize=1)
def _client():
    from google import genai
    from google.genai import types

    return genai.Client(
        api_key=config.GEMINI_API_KEY,
        http_options=types.HttpOptions(timeout=config.GEMINI_TIMEOUT_SECONDS * 1000),
    )


def generate_text(prompt: str, models: list[str]) -> tuple[str, str]:
    """Try each model in order. Returns (text, model_used) or raises GeminiUnavailable."""
    if not is_configured():
        raise GeminiUnavailable("GOOGLE_API_KEY is not set")

    last_error: Exception | None = None
    for model in dict.fromkeys(m for m in models if m):
        try:
            response = _client().models.generate_content(model=model, contents=prompt)
            text = (response.text or "").strip()
            if text:
                return text, model
            last_error = RuntimeError(f"{model} returned an empty response")
        except Exception as exc:  # network, quota, bad model name, missing package...
            log.warning("Gemini call failed for %s: %s", model, exc)
            last_error = exc
    raise GeminiUnavailable(str(last_error))
