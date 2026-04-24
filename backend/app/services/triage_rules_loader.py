from __future__ import annotations

import json
from pathlib import Path

from app.services.triage_rules_schema import TriageRulesFile


def default_rules_path() -> Path:
    return Path(__file__).resolve().parents[1] / "data" / "triage_rules.json"


def load_triage_rules(path: Path | None = None) -> TriageRulesFile:
    p = path or default_rules_path()
    raw = json.loads(p.read_text(encoding="utf-8"))
    return TriageRulesFile.model_validate(raw)
