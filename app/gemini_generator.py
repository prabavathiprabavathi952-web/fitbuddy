"""Gemini Pro: structured 7-day workout plan generation."""
from app import config
from app.gemini_client import GeminiUnavailable, generate_text
from app.offline_plans import build_offline_plan

FORMAT_RULES = """Use EXACTLY this Markdown format and nothing before or after it:

## 7-Day <Goal> Plan (<Intensity> intensity)
One or two sentences summarising the approach.

## Day 1: <Focus of the day>
**Warm-up (5-10 min):** <exercises>
**Main workout:**
- <Exercise> - <sets> x <reps> (rest <seconds>)
- <Exercise> - <sets> x <reps> (rest <seconds>)
**Cooldown / recovery:** <stretches or recovery tip>

(Repeat the same block for Day 2 to Day 7. Rest days are titled "Day N: Rest and recovery" and only list light activity.)

## Important Notes
- 3 to 5 short bullets on progression, form, hydration and when to see a doctor."""


def build_prompt(u: dict) -> str:
    height = f"{u['height']} cm" if u.get("height") else "not given"
    equipment = {"gym": "full gym", "home": "basic home equipment (dumbbells, bands)",
                 "none": "no equipment (bodyweight only)"}.get(u.get("equipment", "gym"), "full gym")
    return f"""You are an experienced, safety-conscious personal trainer.

Create a personalised, structured 7-day workout plan for this person.
- Fitness goal: "{u['goal']}"
- Preferred intensity: {u['intensity']}
- Experience level: {u.get('experience', 'beginner')}
- Available equipment: {equipment}
- Age: {u.get('age', 'not given')}; weight: {u.get('weight', 'not given')} kg; height: {height}
- Extra notes / limitations: {u.get('notes') or 'none'}

Low intensity = 3-4 training days, medium = 5, high = 6, with the remaining days as rest or active recovery.
Choose exercises that suit the experience level and equipment. Respect any injuries or limitations mentioned.

{FORMAT_RULES}"""


def generate_workout(user_input: dict) -> tuple[str, str]:
    """Returns (plan_markdown, source). source is the Gemini model used, or 'offline'."""
    try:
        return generate_text(
            build_prompt(user_input), [config.GEMINI_PRO_MODEL, config.GEMINI_FLASH_MODEL]
        )
    except GeminiUnavailable:
        return build_offline_plan(user_input), "offline"


def generate_workout_gemini(user_input: dict) -> str:
    """Same name as in the project document. Returns just the plan text."""
    return generate_workout(user_input)[0]
