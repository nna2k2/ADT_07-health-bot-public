"""Shared Vietnamese normalization + negation-aware phrase matching for safety/triage."""

from __future__ import annotations

import re
import unicodedata


def normalize_vi(s: str | None) -> str:
    raw = (s or "").lower()
    nfd = unicodedata.normalize("NFD", raw)
    no_marks = "".join(ch for ch in nfd if unicodedata.category(ch) != "Mn")
    ascii_vi = no_marks.replace("đ", "d")
    ascii_vi = re.sub(r"[^a-z0-9\s]", " ", ascii_vi)
    ascii_vi = re.sub(r"\s+", " ", ascii_vi).strip()
    return ascii_vi


_NEGATION_TAIL_RE = re.compile(
    r"(?:^|\s)(?:khong he|chua he|khong thay|khong|ko|chua)"
    r"(?:\s+(?:bi|co|thay))?\s*$"
)


def contains_unnegated_phrase(text: str, phrase: str) -> bool:
    """
    True if `phrase` appears in normalized `text` and is not immediately preceded by negation.
    Example: "khong kho tho" must NOT match phrase "kho tho".
    """
    if not text or not phrase:
        return False
    phrase_tokens = phrase.split()
    if not phrase_tokens:
        return False
    phrase_re = re.compile(r"\b" + r"\s+".join(map(re.escape, phrase_tokens)) + r"\b")
    for m in phrase_re.finditer(text):
        prefix = text[max(0, m.start() - 40) : m.start()].strip()
        prefix_tail = " ".join(prefix.split()[-4:])
        if _NEGATION_TAIL_RE.search(prefix_tail):
            continue
        return True
    return False


def has_unnegated_any(text: str, phrases: list[str]) -> bool:
    return any(contains_unnegated_phrase(text, p) for p in phrases)
