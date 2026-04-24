from __future__ import annotations

from datetime import date

from pydantic import BaseModel


class WeeklySummaryOut(BaseModel):
    user_id: str
    from_date: date
    to_date: date
    checkin_days: int
    avg_sleep_hours: float
    avg_water_liters: float
    avg_steps: float
    # Văn bản thuần số liệu (đầu vào cho chat / hiển thị), không phải lời khuyên rule-based
    stats_text: str

