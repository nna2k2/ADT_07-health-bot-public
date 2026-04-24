"""Pydantic models for data-driven triage_rules.json."""

from __future__ import annotations

from pydantic import BaseModel, Field


class Thresholds(BaseModel):
    medium: float = 20
    high: float = 40
    emergency_score: float = 60


class PatternRule(BaseModel):
    id: str
    phrases: list[str] = Field(min_length=1)
    group: str | None = None
    weight: float = 0
    emergency: bool = False


class FollowUpRule(BaseModel):
    id: str
    if_any_phrase_matched: list[str] = Field(default_factory=list)
    unless_text_contains_any: list[str] = Field(default_factory=list)
    questions: list[str] = Field(min_length=1)


class TriageRulesFile(BaseModel):
    version: str = "1.0.0"
    thresholds: Thresholds = Field(default_factory=Thresholds)
    score_cap_per_group: float = 28
    symptom_groups: dict[str, list[str]] = Field(default_factory=dict)
    patterns: list[PatternRule] = Field(default_factory=list)
    band_actions: dict[str, list[str]] = Field(default_factory=dict)
    follow_up_rules: list[FollowUpRule] = Field(default_factory=list)
    max_follow_up_questions: int = 4
