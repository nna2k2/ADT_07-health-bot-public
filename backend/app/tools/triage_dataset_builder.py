from __future__ import annotations

import argparse
import csv
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class ExampleRow:
    description: str
    patient: str
    doctor_raw: str
    doctor_sanitized: str


_DOSE_RE = re.compile(r"\b\d+(\.\d+)?\s*(mg|mcg|g|ml|iu|units?)\b", re.IGNORECASE)
_FREQ_RE = re.compile(
    r"\b(once|twice|thrice|daily|weekly|per\s+day|every\s+\d+\s*(hours?|days?)|bd|tds|qid)\b",
    re.IGNORECASE,
)
_RX_VERBS_RE = re.compile(
    r"\b(prescribe|start|take|use|apply|continue|stop|dose|dosage|tablet|tab\.|capsule|syrup|injection|antibiotic|steroid)\b",
    re.IGNORECASE,
)
_STRONG_DIAG_RE = re.compile(
    r"\b(you have|this is|it is|it seems you have|the condition is|diagnosis is)\b",
    re.IGNORECASE,
)


def sanitize_doctor_text(text: str) -> str:
    """
    Sanitize Doctor answers into triage-safe style:
    - remove dosing/medication instruction patterns
    - soften certainty language (no diagnosis)
    - keep structure cues / questions / safety advice
    """
    t = (text or "").strip()
    if not t:
        return ""

    # Remove common "consult X online -->" footers
    t = re.sub(r"\bconsult\b.*?online\s*--?>\s*$", "", t, flags=re.IGNORECASE | re.DOTALL).strip()

    # Remove explicit dosages and frequency cues
    t = _DOSE_RE.sub("[liều dùng đã được lược bỏ]", t)
    t = _FREQ_RE.sub("[tần suất đã được lược bỏ]", t)

    # Remove medication/prescription-heavy sentences
    sentences = split_sentences(t)
    kept: list[str] = []
    for s in sentences:
        s_clean = s.strip()
        if not s_clean:
            continue
        # If sentence is strongly about prescribing or dosing, drop it
        if _RX_VERBS_RE.search(s_clean) and (_DOSE_RE.search(s_clean) or _FREQ_RE.search(s_clean)):
            continue
        if re.search(r"\b(paracetamol|ibuprofen|amoxicillin|doxycycline|azithromycin|isotretinoin|fluconazole|sildenafil)\b", s_clean, re.I):
            # generic hard filter for common drug names in this dataset
            continue
        kept.append(s_clean)

    t2 = " ".join(kept).strip()
    if not t2:
        return ""

    # Soften diagnosis certainty
    t2 = _STRONG_DIAG_RE.sub("có thể liên quan đến", t2)
    t2 = re.sub(r"\bdefinitely\b", "có thể", t2, flags=re.IGNORECASE)
    t2 = re.sub(r"\bmost likely\b", "có thể", t2, flags=re.IGNORECASE)

    # Ensure disclaimer
    if "không chẩn đoán" not in t2.lower():
        t2 = (
            t2
            + "\n\nLưu ý: Đây là thông tin tham khảo theo hướng sàng lọc (triage), không phải chẩn đoán. "
            "Bạn nên đi khám nếu triệu chứng nặng lên, kéo dài, hoặc có dấu hiệu bất thường."
        )

    return t2.strip()


def split_sentences(text: str) -> list[str]:
    # Simple sentence splitter for English-ish medical answers.
    # Keeps abbreviations roughly intact by not splitting on common patterns like "mg." etc (already scrubbed).
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z])", text.strip())
    return [p.strip() for p in parts if p.strip()]


def build_examples(csv_path: Path, limit: int) -> list[ExampleRow]:
    rows: list[ExampleRow] = []
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            desc = (r.get("Description") or "").strip()
            patient = (r.get("Patient") or "").strip()
            doctor = (r.get("Doctor") or "").strip()
            if not patient or not doctor:
                continue
            sanitized = sanitize_doctor_text(doctor)
            if not sanitized:
                continue
            rows.append(
                ExampleRow(
                    description=desc,
                    patient=patient,
                    doctor_raw=doctor,
                    doctor_sanitized=sanitized,
                )
            )
            if limit > 0 and len(rows) >= limit:
                break
    return rows


def main() -> None:
    ap = argparse.ArgumentParser(description="Build triage-safe few-shot examples from ai-medical-chatbot.csv")
    ap.add_argument("--input", required=True, help="Path to ai-medical-chatbot.csv")
    ap.add_argument("--output", required=True, help="Output path (.jsonl or .json)")
    ap.add_argument("--limit", type=int, default=200, help="Max examples to export")
    args = ap.parse_args()

    in_path = Path(args.input)
    out_path = Path(args.output)
    examples = build_examples(in_path, args.limit)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.suffix.lower() == ".jsonl":
        with out_path.open("w", encoding="utf-8") as f:
            for ex in examples:
                f.write(json.dumps(asdict(ex), ensure_ascii=False) + "\n")
    else:
        out_path.write_text(json.dumps([asdict(ex) for ex in examples], ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Exported {len(examples)} examples to {out_path}")


if __name__ == "__main__":
    main()

