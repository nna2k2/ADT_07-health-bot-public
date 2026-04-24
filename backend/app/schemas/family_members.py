from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class FamilyMemberOut(BaseModel):
    id: int
    owner_user_id: str
    member_user_id: str
    name: str
    relation: str
    age: int
    gender: str
    height_cm: float
    weight_kg: float
    goal: str
    medical_notes: str
    tracking_note: str
    avatar_bg: str
    facts_text: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FamilyMemberCreate(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    relation: str = Field(default="family", max_length=32)
    age: int = Field(default=0, ge=0, le=120)
    gender: str = Field(min_length=1, max_length=24)
    height_cm: float = Field(ge=50, le=250)
    weight_kg: float = Field(ge=10, le=400)
    goal: str = Field(min_length=1, max_length=255)
    medical_notes: str = Field(default="", max_length=5000)
    tracking_note: str = Field(default="", max_length=255)
    avatar_bg: str = Field(default="#dcfce7", max_length=24)
    facts_text: str = Field(default="", max_length=5000)

