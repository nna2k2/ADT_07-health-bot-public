from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class FewShotExample:
    patient: str
    doctor_sanitized: str


def load_few_shot_examples(path: str | None, limit: int = 6) -> list[FewShotExample]:
    if not path:
        return []
    p = Path(path)
    if not p.exists():
        return []

    examples: list[FewShotExample] = []
    if p.suffix.lower() == ".jsonl":
        # Doc tung dong — KHONG read_text() ca file (JSONL lon se lam treo moi request /chat).
        with p.open(encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not isinstance(obj, dict):
                    continue
                patient = (obj.get("patient") or "").strip()
                doctor = (obj.get("doctor_sanitized") or "").strip()
                if patient and doctor:
                    examples.append(FewShotExample(patient=patient, doctor_sanitized=doctor))
                if len(examples) >= limit:
                    break
        return examples

    data = json.loads(p.read_text(encoding="utf-8"))
    if isinstance(data, list):
        for obj in data:
            if not isinstance(obj, dict):
                continue
            patient = (obj.get("patient") or "").strip()
            doctor = (obj.get("doctor_sanitized") or "").strip()
            if patient and doctor:
                examples.append(FewShotExample(patient=patient, doctor_sanitized=doctor))
            if len(examples) >= limit:
                break
    return examples


def format_examples_for_prompt(examples: list[FewShotExample]) -> str:
    if not examples:
        return ""
    blocks: list[str] = []
    blocks.append(
        "Ví dụ tham khảo (đã được làm sạch theo triage: không kê đơn, không chẩn đoán chắc chắn). "
        "Hãy học văn phong + cấu trúc, không sao chép máy móc."
    )
    for i, ex in enumerate(examples, start=1):
        blocks.append(f"\n[Ví dụ {i}]\nUser:\n{ex.patient}\n\nAssistant (triage-safe):\n{ex.doctor_sanitized}")
    return "\n".join(blocks).strip()

