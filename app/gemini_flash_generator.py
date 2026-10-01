"""Gemini Flash: fast nutrition / recovery tips."""
from app import config
from app.gemini_client import GeminiUnavailable, generate_text
from app.nutrition import fallback_tip


def generate_nutrition_tip(goal: str) -> tuple[str, str]:
    """Returns (tip, source). Falls back to a built-in tip if Gemini is unavailable."""
    prompt = (
        f"Give one clear, helpful nutrition or recovery tip for someone whose fitness goal is "
        f"\"{goal}\". Keep it practical, friendly and under 50 words. Plain text only: "
        f"no markdown, no headings, no preamble."
    )
    try:
        text, model = generate_text(prompt, [config.GEMINI_FLASH_MODEL, config.GEMINI_PRO_MODEL])
        return text.strip(), model
    except GeminiUnavailable:
        return fallback_tip(goal), "offline"


def generate_nutrition_tip_with_flash(goal: str) -> str:
    """Same name as in the project document. Returns just the tip text."""
    return generate_nutrition_tip(goal)[0]
