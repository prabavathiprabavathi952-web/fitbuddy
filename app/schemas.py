"""Pydantic models used to validate user input (forms and JSON API)."""
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator

Intensity = Literal["low", "medium", "high"]
Experience = Literal["beginner", "intermediate", "advanced"]
Equipment = Literal["gym", "home", "none"]


class _Normalised(BaseModel):
    @field_validator("intensity", "experience", "equipment", check_fields=False, mode="before")
    @classmethod
    def _lower(cls, v):
        return v.strip().lower() if isinstance(v, str) else v


class UserInput(_Normalised):
    user_id: Optional[int] = Field(None, ge=1, le=10_000_000)
    username: str = Field(..., min_length=1, max_length=80)
    age: int = Field(..., ge=10, le=100)
    weight: float = Field(..., ge=20, le=400, description="kg")
    height: Optional[float] = Field(None, ge=80, le=250, description="cm")
    goal: str = Field(..., min_length=2, max_length=200)
    intensity: Intensity
    experience: Experience = "beginner"
    equipment: Equipment = "gym"
    notes: Optional[str] = Field(None, max_length=500)

    @field_validator("username", "goal")
    @classmethod
    def _strip(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("must not be blank")
        return v


class FeedbackRequest(BaseModel):
    feedback: str = Field(..., min_length=3, max_length=1000)

    @field_validator("feedback")
    @classmethod
    def _strip(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 3:
            raise ValueError("feedback is too short")
        return v


class WorkoutRequest(_Normalised):
    goal: str = Field(..., min_length=2, max_length=200)
    intensity: Intensity
    experience: Experience = "beginner"
