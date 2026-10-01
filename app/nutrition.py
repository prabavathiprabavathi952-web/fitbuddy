"""Nutrition helpers: offline tips, BMI and hydration targets."""
import random
from typing import Optional

_TIPS = {
    "fat_loss": [
        "Build each meal around lean protein and vegetables. They keep you full for longer on fewer calories.",
        "Drink a glass of water before meals and keep sugary drinks to a minimum. It makes portion control easier.",
        "Aim for 7-9 hours of sleep. Poor sleep raises hunger hormones and makes late-night snacking more likely.",
    ],
    "muscle": [
        "Include 20-30 g of protein within a couple of hours after training, such as eggs, chicken, paneer, dal, or Greek yogurt.",
        "Spread protein across 3-4 meals rather than eating it all at dinner. Muscle repair works best with steady supply.",
        "Add a carbohydrate source like rice, oats, or potatoes around workouts to fuel lifting and speed recovery.",
    ],
    "general": [
        "Fill half your plate with colourful vegetables and fruit, and keep processed snacks for occasional treats.",
        "Stay hydrated through the day. Pale-yellow urine is a simple sign you are drinking enough.",
        "Take a 10-minute walk after meals. It helps digestion and steadies blood sugar.",
    ],
}


def goal_category(goal: str) -> str:
    g = (goal or "").lower()
    if any(k in g for k in ("lose", "loss", "fat", "slim", "cut", "weight", "belly")):
        return "fat_loss"
    if any(k in g for k in ("muscle", "gain", "bulk", "strength", "mass", "build")):
        return "muscle"
    return "general"


def fallback_tip(goal: str) -> str:
    return random.choice(_TIPS[goal_category(goal)])


def calculate_bmi(weight_kg: float, height_cm: Optional[float]) -> Optional[float]:
    if not height_cm or height_cm <= 0:
        return None
    m = height_cm / 100
    return round(weight_kg / (m * m), 1)


def bmi_category(bmi: Optional[float]) -> Optional[str]:
    if bmi is None:
        return None
    if bmi < 18.5:
        return "Below typical range"
    if bmi < 25:
        return "Typical range"
    if bmi < 30:
        return "Above typical range"
    return "Well above typical range"


def water_target_litres(weight_kg: float) -> float:
    """Rough daily water target: about 33 ml per kg of body weight."""
    return round(weight_kg * 0.033, 1)
