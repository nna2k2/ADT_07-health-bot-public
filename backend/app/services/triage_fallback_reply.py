"""Structured Vietnamese reply when the LLM returns empty text (still not a diagnosis)."""

from __future__ import annotations

from app.services.negation_utils import normalize_vi
from app.services.triage_service import TriageResult, is_orthostatic_dizziness


def wellness_fallback_reply(triage: TriageResult, user_message: str = "") -> str:
    ortho = is_orthostatic_dizziness(normalize_vi(user_message))
    intro = (
        "Bạn mô tả **chóng mặt khi đứng lên** — mình gợi ý sàng lọc tham khảo (không phải chẩn đoán chắc chắn):"
        if ortho
        else "Dựa trên mô tả của bạn, đây là **gợi ý sàng lọc tham khảo** (không phải chẩn đoán chắc chắn):"
    )
    lines: list[str] = [intro, "", "**Một số hướng thường gặp (tham khảo):**"]
    for c in triage.possible_causes:
        lines.append(f"- {c}")
    if ortho:
        lines.extend(
            [
                "",
                "**Gợi ý self-care ngắn:**",
                "- Đứng dậy từ từ, ngồi vài giây trước khi đi.",
                "- Uống đủ nước trong ngày (trừ khi bác sĩ hạn chế).",
                "- Ăn uống đều, tránh nhịn đói lâu.",
                "- Ghi lại tần suất và điều làm nặng/nhẹ để theo dõi.",
            ]
        )
    lines.extend(["", "**Việc nên cân nhắc:**"])
    for a in triage.suggested_actions:
        lines.append(f"- {a}")
    if triage.follow_up_questions:
        lines.extend(["", "**Để làm rõ thêm, bạn có thể cho mình biết:**"])
        for q in triage.follow_up_questions[:5]:
            lines.append(f"- {q}")
    lines.extend(["", _when_to_seek_care(triage.risk_level, ortho=ortho)])
    return "\n".join(lines).strip()


def _when_to_seek_care(risk: str, *, ortho: bool = False) -> str:
    if ortho:
        return (
            "**Nên đi khám / cấp cứu nếu có:** ngất hoặc suýt ngất; đau ngực; khó thở; tim đập rất nhanh/không yên; "
            "té ngã; triệu chứng nặng dần hoặc tái diễn thường xuyên. "
            "Nếu nghi ngờ cấp cứu, gọi số cấp cứu hoặc đến cơ sở y tế gần nhất."
        )
    if risk == "emergency":
        return (
            "**Khi nào cần cấp cứu / đi ngay:** nếu có dấu hiệu nguy hiểm đột ngột (ví dụ khó thở nặng, "
            "đau ngực lan, co giật, bất tỉnh, yếu liệt một bên, chảy máu ồ ạt). Nếu đang khẩn cấp, hãy gọi cấp cứu."
        )
    if risk == "high":
        return (
            "**Khi nào cần đi khám sớm:** triệu chứng nặng lên nhanh, xuất hiện dấu hiệu thần kinh mới, "
            "sốt cao kèm cứng cổ, hoặc bạn cảm thấy không an toàn — nên đến cơ sở y tế trong 24 giờ."
        )
    return (
        "**Khi nào nên đi khám:** triệu chứng kéo dài không đỡ, tái phát thường xuyên, ảnh hưởng sinh hoạt, "
        "hoặc bạn lo lắng — nên được bác sĩ khám trực tiếp. **Cấp cứu** nếu có dấu hiệu nguy hiểm đột ngột như trên."
    )
