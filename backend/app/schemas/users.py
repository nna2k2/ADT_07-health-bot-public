from __future__ import annotations

from pydantic import BaseModel, Field


class UserOnboardingIn(BaseModel):
    user_id: str = Field(min_length=1, max_length=64)
    age: int = Field(ge=1, le=120)
    gender: str = Field(min_length=1, max_length=24)
    height_cm: float = Field(ge=50, le=250)
    weight_kg: float = Field(ge=10, le=400)
    goal: str = Field(min_length=1, max_length=255)
    medical_notes: str = Field(default="", max_length=5000)


class UserOut(BaseModel):
    user_id: str
    age: int
    gender: str
    height_cm: float
    weight_kg: float
    goal: str
    medical_notes: str

