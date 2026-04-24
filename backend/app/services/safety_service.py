from __future__ import annotations

from app.services.negation_utils import contains_unnegated_phrase, normalize_vi


EMERGENCY_KEYWORDS = [
    "đau ngực",
    "khó thở",
    "ngất",
    "co giật",
    "chảy máu nhiều",
    "tự tử",
    "tự làm hại bản thân",
]


def check_safety(message: str) -> tuple[bool, str | None]:
    text = normalize_vi(message)
    for kw in EMERGENCY_KEYWORDS:
        kw_norm = normalize_vi(kw)
        if contains_unnegated_phrase(text, kw_norm):
            return False, kw
    return True, None


def emergency_reply(keyword: str | None = None) -> str:
    kw = f" (từ khóa: “{keyword}”)" if keyword else ""
    return (
        "Mình lo ngại những gì bạn mô tả có thể là dấu hiệu nghiêm trọng"
        f"{kw}. Bot này chỉ hỗ trợ chăm sóc sức khỏe tổng quát, **không thay thế bác sĩ**.\n\n"
        "- Nếu bạn đang ở tình trạng khẩn cấp, hãy **gọi cấp cứu** hoặc đến **cơ sở y tế gần nhất ngay**.\n"
        "- Nếu có thể, hãy nhờ người thân ở cạnh bạn.\n\n"
        "Bạn có muốn mình giúp bạn liệt kê nhanh các thông tin cần nói với nhân viên y tế (triệu chứng, thời điểm bắt đầu, mức độ, bệnh nền, thuốc đang dùng) không?"
    )
