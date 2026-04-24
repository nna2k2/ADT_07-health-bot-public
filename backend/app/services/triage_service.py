"""Data-driven triage: scoring engine + symptom groups + follow-up questions (not a diagnosis)."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from app.core.config import settings
from app.services.negation_utils import contains_unnegated_phrase, normalize_vi
from app.services.triage_rules_loader import default_rules_path, load_triage_rules
from app.services.triage_rules_schema import TriageRulesFile

RiskLevel = str  # "low" | "medium" | "high" | "emergency"

# Normalized (ASCII) phrases: chóng mặt/choáng khi đứng — ưu tiên ngữ cảnh tụt HA tư thế, không gộp migraine/cổ.
_ORTHOSTATIC_DIZZY_PHRASES: tuple[str, ...] = tuple(
    normalize_vi(p)
    for p in (
        "chóng mặt khi đứng",
        "chóng mặt khi đứng lên",
        "chóng mặt lúc đứng",
        "hay chóng mặt khi đứng",
        "choáng khi đứng lên",
        "choáng mặt khi đứng",
        "chóng mặt khi đứng dậy",
    )
)


def is_orthostatic_dizziness(normalized_text: str) -> bool:
    if not normalized_text:
        return False
    return any(contains_unnegated_phrase(normalized_text, ph) for ph in _ORTHOSTATIC_DIZZY_PHRASES)


@dataclass(frozen=True)
class TriageResult:
    risk_level: RiskLevel
    score: float
    suggested_actions: list[str]
    possible_causes: list[str]
    follow_up_questions: list[str]
    reason_codes: list[str]
    rules_version: str


def _rules_file_path() -> Path:
    if settings.triage_rules_path:
        return Path(settings.triage_rules_path)
    return default_rules_path()


@lru_cache(maxsize=1)
def _cached_rules(path_str: str) -> TriageRulesFile:
    return load_triage_rules(Path(path_str))


def get_rules() -> TriageRulesFile:
    return _cached_rules(str(_rules_file_path().resolve()))


def invalidate_rules_cache() -> None:
    _cached_rules.cache_clear()


def triage_message(message: str) -> TriageResult:
    rules = get_rules()
    text = normalize_vi(message)
    return _evaluate(text, rules)


def _evaluate(normalized_text: str, rules: TriageRulesFile) -> TriageResult:
    reason_codes: list[str] = []
    emergency_hit = False
    group_weights: dict[str, float] = {}
    matched_groups: set[str] = set()

    for p in rules.patterns:
        matched = False
        for phrase in p.phrases:
            ph = normalize_vi(phrase)
            if contains_unnegated_phrase(normalized_text, ph):
                matched = True
                break
        if not matched:
            continue

        reason_codes.append(f"hit:{p.id}")
        if p.group:
            matched_groups.add(p.group)

        if p.emergency:
            emergency_hit = True
            reason_codes.append(f"emergency:{p.id}")
            continue

        g = p.group or "general"
        group_weights[g] = group_weights.get(g, 0.0) + float(p.weight)

    for g, w in list(group_weights.items()):
        cap = float(rules.score_cap_per_group)
        if w > cap:
            group_weights[g] = cap
            reason_codes.append(f"cap:{g}")

    score = sum(group_weights.values())
    score = min(score, 100.0)

    if emergency_hit:
        risk: RiskLevel = "emergency"
        reason_codes.append("band:emergency_pattern")
    elif score >= rules.thresholds.emergency_score:
        risk = "emergency"
        reason_codes.append("band:emergency_score")
    elif score >= rules.thresholds.high:
        risk = "high"
        reason_codes.append("band:high")
    elif score >= rules.thresholds.medium:
        risk = "medium"
        reason_codes.append("band:medium")
    else:
        risk = "low"
        reason_codes.append("band:low")

    actions = list(rules.band_actions.get(risk) or [])
    if not actions:
        actions = [
            "Theo dõi triệu chứng và ghi lại diễn biến.",
            "Nếu lo lắng hoặc triệu chứng thay đổi, hãy cân nhắc đi khám.",
        ]

    causes = _collect_causes(rules, matched_groups, normalized_text)
    follow_ups = _collect_follow_ups(rules, normalized_text)

    return TriageResult(
        risk_level=risk,
        score=round(score, 2),
        suggested_actions=actions,
        possible_causes=causes,
        follow_up_questions=follow_ups,
        reason_codes=reason_codes[:32],
        rules_version=rules.version,
    )


def _collect_causes(rules: TriageRulesFile, matched_groups: set[str], normalized_text: str) -> list[str]:
    if is_orthostatic_dizziness(normalized_text):
        ortho = list(rules.symptom_groups.get("orthostatic", []))
        if ortho:
            return ortho[:6]

    causes: list[str] = []
    groups = set(matched_groups)
    if not groups:
        groups.add("general")

    for g in groups:
        causes.extend(rules.symptom_groups.get(g, []))

    if not causes:
        causes = list(rules.symptom_groups.get("general", []))

    dedup: list[str] = []
    seen: set[str] = set()
    for c in causes:
        if c not in seen:
            seen.add(c)
            dedup.append(c)
    return dedup[:6]


def _collect_follow_ups(rules: TriageRulesFile, normalized_text: str) -> list[str]:
    out: list[str] = []
    for rule in rules.follow_up_rules:
        if not any(contains_unnegated_phrase(normalized_text, normalize_vi(p)) for p in rule.if_any_phrase_matched):
            continue
        if rule.unless_text_contains_any and any(
            normalize_vi(x) in normalized_text for x in rule.unless_text_contains_any
        ):
            continue
        out.extend(rule.questions)
        if len(out) >= rules.max_follow_up_questions:
            break
    return out[: rules.max_follow_up_questions]
