from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class CheckinIn(BaseModel):
    user_id: str = Field(min_length=1, max_length=64)
    sleep_hours: float = Field(ge=0, le=24)
    water_liters: float = Field(ge=0, le=20)
    steps: int = Field(ge=0, le=200_000)
    mood: str = Field(min_length=1, max_length=64)
    symptoms: str = Field(default="", max_length=5000)


class CheckinOut(BaseModel):
    id: int
    user_id: str
    sleep_hours: float
    water_liters: float
    steps: int
    mood: str
    symptoms: str
    created_at: datetime

