from __future__ import annotations

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=64)
    message: str = Field(min_length=1, max_length=4000)


class ChatResponse(BaseModel):
    reply: str
    intent: str | None = None
    # Gợi ý điều hướng trong SPA (Angular), ví dụ đặt lịch → /doctors
    cta_label: str | None = None
    cta_path: str | None = None
    # Chỉ gửi cho UI khi intent là tư vấn triệu chứng / khẩn cấp.
    # Nếu None, frontend sẽ không hiển thị “Mức độ: …”.
    risk_level: str | None = None
    triage_score: float | None = None
    suggested_actions: list[str] = []
    possible_causes: list[str] = []
    follow_up_questions: list[str] = []
    reason_codes: list[str] = []
    rules_version: str | None = None
    blocked: bool = False
    reason: str | None = None

