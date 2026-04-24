"""Intent routing + memory policy + per-intent LLM instructions (rule-based, Vietnamese)."""

from __future__ import annotations

import re

from app.services.negation_utils import normalize_vi
from app.services.triage_service import TriageResult, is_orthostatic_dizziness

INTENT_GREETING = "greeting"
INTENT_GENERAL_WELLNESS = "general_wellness"
INTENT_LAB_MEDIA = "lab_media"
INTENT_BOOKING = "booking"
INTENT_DOCTOR_AVAILABILITY = "doctor_availability"
INTENT_MEDICATION_REMINDER = "medication_reminder"
INTENT_SYMPTOM_ADVICE = "symptom_advice"
INTENT_EMERGENCY = "emergency"
INTENT_SUMMARY = "summary"
INTENT_OUT_OF_SCOPE = "out_of_scope"

_OUT_OF_SCOPE_PATTERNS = [
    "ke don",
    "don thuoc",
    "thuoc gi",
    "lieu luong",
    "chan doan chac",
    "chac chan la benh",
    "mo xam",
    "phau thuat tai nha",
    "tu sat",
    "lam hai nguoi khac",
]

_BOOKING_PATTERNS = [
    "dat lich",
    "hen kham",
    "dang ky kham",
    "book lich",
    "lich kham",
    "dat hen",
    "muon kham",
    "dang ky hen",
]

_DOCTOR_AVAIL_PATTERNS = [
    "bac si co mat",
    "co bac si",
    "lich lam viec",
    "khung gio kham",
    "gio lam viec",
    "hom nay co kham",
    "ngay mai co kham",
    "phong kham mo cua",
    "bac si nao",
]

_MEDICATION_REMINDER_PATTERNS = [
    "nhac uong thuoc",
    "nhac thuoc",
    "hen gio uong thuoc",
    "hen gio thuoc",
    "dat nhac uong thuoc",
    "tao nhac uong thuoc",
    "tao nhac thuoc",
    "tao nhac nho uong thuoc",
    "tao loi nhac uong thuoc",
    "nhac nho uong thuoc",
    "nhac nho thuoc",
    "bao thuc uong thuoc",
    "bao gio uong thuoc",
]

# Nguoi dung yeu cau doc phieu xet nghiem / anh ket qua (co dinh kem anh).
_LAB_DOC_READ_PATTERNS = [
    "xet nghiem",
    "phieu kham",
    "phieu xet",
    "ket qua kham",
    "chi so",
    "tham chieu",
    "bat thuong",
    "danh gia",
    "doc ky",
    "doc anh",
    "trong anh",
    "trich",
    "bang ",
    "don vi",
    "muc do uu tien",
    "uu tien",
    "liet ke",
]

_SUMMARY_PATTERNS = [
    "tom tat",
    "tong ket",
    "ho so cua toi",
    "thong tin cua toi",
    "bao cao tuan",
    "tuan nay the nao",
    "check in cua toi",
    "ket qua check in",
]

_SYMPTOM_HINT_PATTERNS = [
    "dau ",
    " dau",
    "sot",
    "met moi",
    "met ",
    "non ",
    "buon non",
    "tieu ",
    "ho ",
    "so mui",
    "chay mui",
    "dau bung",
    "dau nguc",
    "kho tho",
    "chong mat",
    "choang",
    "trieu chung",
    "cam thay khong khoe",
    "benh",
]

_GREETING_ONLY = re.compile(
    r"^(xa loi\s*)?(xin\s+)?chao(\s+ban|\s+bac|\s+anh|\s+chi|\s+em|\s+cau|\s+co)?\s*!?\s*$"
    r"|^(hi|hello|hey|good morning|chao)\b[!.\s]*$",
    re.IGNORECASE,
)


def _has_any(t: str, pats: list[str]) -> bool:
    return any(p in t for p in pats)


def user_explicitly_requests_profile(t: str) -> bool:
    phrases = [
        "ho so",
        "thong tin cua toi",
        "profile cua toi",
        "onboarding cua toi",
        "tuoi cua toi",
        "can nang cua toi",
        "chieu cao cua toi",
        "check in cua toi",
        "checkin cua toi",
        "muc tieu cua toi",
        "ghi chu y te cua toi",
        "du lieu cua toi",
        "tinh hinh cua toi",
        "dua vao ho so",
        "theo ho so cua toi",
    ]
    return any(p in t for p in phrases)


def _has_image_attachments(media_attachments: list[dict] | None) -> bool:
    if not media_attachments:
        return False
    return any(isinstance(x, dict) and x.get("type") == "image_url" for x in media_attachments)


def _is_lab_document_read_request(t: str) -> bool:
    if _has_any(t, _LAB_DOC_READ_PATTERNS):
        return True
    return "doc " in t and "anh" in t


def _assistant_recently_lab_like(conversation_history: list[dict[str, str]] | None) -> bool:
    """Gan day co ban assistant tra loi dang bang xet nghiem / chi so."""
    if not conversation_history:
        return False
    tail = conversation_history[-6:]
    parts: list[str] = []
    for m in tail:
        if m.get("role") != "assistant":
            continue
        c = m.get("content")
        if isinstance(c, str) and c.strip():
            parts.append(c)
    if not parts:
        return False
    blob = normalize_vi("\n".join(parts))
    if blob.count("|") < 3:
        return False
    markers = ("mmol", "mg/dl", "u/l", "huyet", "cholesterol", "glucose", "creatin", "bmi", "alt")
    return any(x in blob for x in markers)


def _lab_followup_cues(t: str) -> bool:
    """Nguoi dung dang hoi tiep ve chi so / uu tien / cai thien — khong phai mo ta trieu chung moi."""
    cues = (
        "chi so",
        "ket qua",
        "cai thien",
        "uu tien",
        "truoc mat",
        "theo doi",
        "phan nao",
        "quan trong",
        "ket luan",
        "tom tat",
        "giai thich them",
        "nhung chi so",
        "cac chi so",
        "chi so tren",
        "bang tren",
        "nen lam gi",
        "cap cuu hay",
        "di kham",
        "phan tich",
    )
    if any(c in t for c in cues):
        return True
    # "dau dau toi can ket qua luon" — met phien, van can noi vao ket qua da co
    if "ket qua" in t and len(t) < 96:
        return True
    return False


def _lab_table_thread_followup(
    conversation_history: list[dict[str, str]] | None,
    message: str,
    triage: TriageResult,
) -> bool:
    """
    Tiep noi sau ban phan tich chi so: khong ep sang symptom_advice chi vi co tu 'dau'
    hoac triage nhe.
    """
    if not conversation_history:
        return False
    t = normalize_vi(message)
    if not _assistant_recently_lab_like(conversation_history):
        return False
    if not _lab_followup_cues(t):
        return False
    if triage.risk_level == "emergency":
        return False
    if triage.risk_level in ("high", "medium") and triage.score >= 12:
        return False
    if "kho tho" in t or "dau nguc" in t or "co giat" in t or "bat tinh" in t:
        return False
    return True


def should_include_profile(*, intent: str, message: str) -> bool:
    t = normalize_vi(message)
    if intent == INTENT_SUMMARY:
        return True
    if user_explicitly_requests_profile(t):
        return True
    if intent in (INTENT_BOOKING, INTENT_DOCTOR_AVAILABILITY, INTENT_GREETING, INTENT_OUT_OF_SCOPE):
        return False
    if intent == INTENT_GENERAL_WELLNESS:
        return False
    if intent == INTENT_LAB_MEDIA:
        return False
    if intent == INTENT_SYMPTOM_ADVICE:
        return False
    if intent == INTENT_EMERGENCY:
        return False
    return False


def classify_intent(
    message: str,
    triage: TriageResult,
    *,
    media_attachments: list[dict] | None = None,
    conversation_history: list[dict[str, str]] | None = None,
) -> str:
    t = normalize_vi(message)
    if triage.risk_level == "emergency":
        return INTENT_EMERGENCY
    if _has_any(t, _OUT_OF_SCOPE_PATTERNS):
        return INTENT_OUT_OF_SCOPE
    if _has_any(t, _SUMMARY_PATTERNS):
        return INTENT_SUMMARY
    if _has_any(t, _BOOKING_PATTERNS):
        return INTENT_BOOKING
    if _has_any(t, _DOCTOR_AVAIL_PATTERNS):
        return INTENT_DOCTOR_AVAILABILITY
    if _has_any(t, _MEDICATION_REMINDER_PATTERNS):
        return INTENT_MEDICATION_REMINDER
    if _has_image_attachments(media_attachments) and _is_lab_document_read_request(t):
        return INTENT_LAB_MEDIA
    if _lab_table_thread_followup(conversation_history, message, triage):
        return INTENT_GENERAL_WELLNESS
    if _has_symptom_hint(t) or triage.risk_level in ("high", "medium") or triage.score >= 8:
        return INTENT_SYMPTOM_ADVICE
    stripped = t.strip()
    if len(stripped) <= 48 and _GREETING_ONLY.match(stripped.replace("  ", " ")):
        return INTENT_GREETING
    # Mac dinh KHONG phai phong van trieu chung: hoi tiep sau anh/xet nghiem, loi khuyen chung...
    return INTENT_GENERAL_WELLNESS


def _has_symptom_hint(t: str) -> bool:
    return _has_any(t, _SYMPTOM_HINT_PATTERNS)


def include_triage_in_prompt(intent: str) -> bool:
    return intent in (INTENT_SYMPTOM_ADVICE, INTENT_EMERGENCY)


def intent_llm_addon(intent: str, triage: TriageResult, message: str = "") -> str:
    if intent == INTENT_GREETING:
        return (
            "Ý định: chào hỏi — Chào ngắn gọn, thân thiện. Hỏi một câu bạn có thể giúp gì "
            "(wellness / sàng lọc / đặt lịch demo). Không liệt kê hồ sơ, không hỏi triệu chứng nếu người dùng chưa nói.\n"
            "Bắt buộc: Trả lời bằng tiếng Việt có dấu, tự nhiên."
        )
    if intent == INTENT_LAB_MEDIA:
        return (
            "Ý định: lab_media — Người dùng gửi ẢNH phiếu xét nghiệm / kết quả khám / tài liệu y tế và yêu cầu đọc chi tiết.\n"
            "Bắt buộc tuân theo đúng thứ tự và cấu trúc họ yêu cầu (nếu họ đánh số 1. 2. 3. thì trả lời đúng thứ tự đó).\n"
            "Nếu họ yêu cầu bảng: dùng markdown bảng với cột Tên chỉ số | Kết quả | Đơn vị | Khoảng tham chiếu | Đánh giá (thấp/bình thường/cao hoặc tương đương).\n"
            "Liệt kê riêng các chỉ số bất thường so với khoảng tham chiếu (nếu đọc được trên ảnh). Nếu tất cả bình thường, nói rõ.\n"
            "Phần giải thích ngắn từng chỉ số bất thường: chỉ là hướng tham khảo giáo dục, không chẩn đoán bệnh, không kê đơn.\n"
            "Xếp mức độ ưu tiên đúng 3 nhóm nếu họ yêu cầu (cấp cứu ngay / nên đi khám sớm / chỉ cần theo dõi) — chỉ dựa trên nội dung đọc được trên ảnh, không suy diễn.\n"
            "Nếu ảnh mờ, lóa, cắt lề, che khuất: chỉ rõ dòng hoặc mục nào không đọc được; tuyệt đối không nói chung chung kiểu «không rõ thông tin» mà không chỉ mục cụ thể.\n"
            "Tuyệt đối không trả lời bằng mẫu «gợi ý sàng lọc triệu chứng» (căng thẳng, thiếu ngủ, nguyên nhân chung chung) nếu họ đang yêu cầu đọc phiếu xét nghiệm.\n"
            "Bắt buộc: Tiếng Việt có dấu, tự nhiên; nhắc lại đây không phải chẩn đoán và không thay bác sĩ."
        )
    if intent == INTENT_GENERAL_WELLNESS:
        return (
            "Ý định: general_wellness — Hội thoại tổng quát hoặc tiếp nối lượt trả lời trước (ví dụ sau khi gửi ảnh/kết quả xét nghiệm). "
            "Nếu người dùng dùng đại từ như «nó», «thế», «phần nào quan trọng nhất», «ưu tiên», «kết quả đó» thì hiểu là trở lại nội dung các tin nhắn trước đó; "
            "không mở phỏng vấn triệu chứng từ đầu (kiểu «triệu chứng cụ thể là gì») nếu họ không mô tả triệu chứng mới. "
            "Nếu ngữ cảnh là ảnh hoặc kết quả khám: tiếp tục hướng dẫn giáo dục, hướng xử lý thực tế (theo dõi, đời sống, khi nào nên gặp bác sĩ), "
            "tóm tắt ngắn nếu cần; không chẩn đoán chắc chắn, không kê đơn.\n"
            "Bắt buộc: Trả lời bằng tiếng Việt có dấu, tự nhiên."
        )
    if intent == INTENT_BOOKING:
        return (
            "Ý định: đặt lịch — Người dùng muốn đặt lịch khám.\n"
            "Trả lời cho người dùng: tiếng Việt có dấu, ngắn, thân thiện (khoảng 2–4 câu nếu đủ).\n"
            "Nói ngắn: trong app có bước chọn bác sĩ, chọn ngày và giờ trống, rồi điền họ tên / email / SĐT để gửi yêu cầu (demo).\n"
            "Hướng dẫn vào màn đặt lịch: chỉ nói bằng lời thường — ví dụ mở mục **Danh sách bác sĩ** hoặc **Đặt lịch** trên menu / trang chính app. "
            "Nếu họ hỏi «ở đâu»: chỉ cần chỉ rõ là mục trên menu hoặc màn tương tự bằng tên tiếng Việt, không nhắc URL, không nhắc «đường dẫn», không tiếng Anh kỹ thuật.\n"
            "Nếu họ chưa nói chuyên khoa hoặc ngày giờ mong muốn: chỉ hỏi thêm **một** câu ngắn gộp lại (ví dụ chuyên khoa và ngày/giờ ưu tiên) để họ dễ chọn trên màn đặt lịch — không tách nhiều câu hỏi dài.\n"
            "Không hỏi phòng khám / khu vực. Không bịa tên bác sĩ hay giờ cụ thể. Không tư vấn sức khỏe / triệu chứng / kê đơn / chẩn đoán.\n"
            "Bắt buộc: Toàn bộ nội dung trả cho người dùng bằng tiếng Việt có dấu."
        )
    if intent == INTENT_DOCTOR_AVAILABILITY:
        return (
            "Ý định: hỏi lịch / bác sĩ — Họ hỏi lịch hoặc bác sĩ.\n"
            "Trả lời: tiếng Việt có dấu, ngắn, thân thiện. Trong app họ xem danh sách bác sĩ và giờ trống sau khi chọn bác sĩ + ngày trên màn đặt lịch.\n"
            "Hướng dẫn: mở mục **Danh sách bác sĩ** hoặc **Đặt lịch** (menu / trang chính). Không nhắc URL hay «đường dẫn», không tiếng Anh kỹ thuật.\n"
            "Nếu họ hỏi chung: một câu ngắn hỏi chuyên khoa hoặc ngày trong tuần họ quan tâm.\n"
            "Không bịa tên bác sĩ hay giờ. Không tư vấn y. Bắt buộc: tiếng Việt có dấu."
        )
    if intent == INTENT_MEDICATION_REMINDER:
        return (
            "Ý định: nhắc uống thuốc — Người dùng muốn tạo nhắc nhở uống thuốc trong app.\n"
            "Trả lời: tiếng Việt có dấu, ngắn, thân thiện.\n"
            "Hướng dẫn: vào mục **Nhắc nhở** → bấm **+ Mới** → chọn loại **💊 Uống thuốc** → đặt thời gian.\n"
            "Nếu người dùng chưa nói giờ: hỏi 1 câu ngắn về giờ (và tên thuốc nếu muốn).\n"
            "Không kê đơn, không tư vấn liều lượng."
        )
    if intent == INTENT_SYMPTOM_ADVICE:
        t = normalize_vi(message)
        if is_orthostatic_dizziness(t):
            return (
                "Ngữ cảnh đặc biệt: chóng mặt / choáng khi đứng lên (đổi tư thế). Bám sát mô tả này.\n"
                "- Ưu tiên hướng tham khảo: tụ huyết áp tư thế, mất nước, thiếu máu, ăn uống kém, tác dụng phụ thuốc (hạ áp, lợi tiểu…). "
                "Không liệt kê migraine / cổ vai gáy / đau đầu căng thẳng nếu người dùng không nói tới các dấu hiệu đó.\n"
                "- Hỏi 3–5 câu làm rõ: có ngất/suýt ngất; đau ngực / khó thở / tim đập nhanh; mất nước / sốt / tiêu chảy / ăn uống kém; "
                "thuốc hạ áp hoặc lợi tiểu; triệu chứng kéo dài bao lâu và tần suất.\n"
                "- Tự chăm sóc ngắn: đứng dậy từ từ, uống đủ nước, ăn đều, theo dõi nếu tái diễn.\n"
                "- Dấu hiệu cần đi khám / cấp cứu phù hợp: ngất, đau ngực, khó thở, tim đập nhanh nhiều, té ngã, "
                "triệu chứng nặng dần hoặc tái diễn thường xuyên.\n"
                "- Trả lời ngắn, thân thiện, tự nhiên; không chẩn đoán chắc chắn; không tiết lộ risk_level/triage_score.\n"
                "Bắt buộc: Trả lời bằng tiếng Việt có dấu."
            )
        if triage.risk_level == "low":
            return (
                "Ý định: symptom_advice (mức nhẹ) — Tập trung khuyến nghị chăm sóc cơ bản (ngủ, nước, nghỉ, theo dõi). "
                "Hỏi thêm các dấu hiệu cảnh báo (red flags) phù hợp ngữ cảnh "
                "(ví dụ: yếu liệt, khó thở, đau ngực, sốt cao, cứng cổ, ý định tự hại…). "
                "Chỉ khuyên cấp cứu / đi ngay khi có dấu hiệu nặng hoặc triage cao — không tự leo thang nếu mô tả nhẹ và ổn định.\n"
                "Bắt buộc: Trả lời bằng tiếng Việt có dấu; tuân theo system_prompt về an toàn (không chẩn đoán chắc, không kê đơn)."
            )
        return (
            "Ý định: symptom_advice — Ưu tiên làm rõ triệu chứng và khuyên đi khám sớm khi mức rủi ro trung bình / cao. "
            "Hỏi red flags. Không chẩn đoán chắc chắn, không kê đơn.\n"
            "Bắt buộc: Trả lời bằng tiếng Việt có dấu."
        )
    if intent == INTENT_EMERGENCY:
        return (
            "Ý định: emergency — Ưu tiên an toàn: khuyên gọi cấp cứu hoặc đến cơ sở y tế ngay nếu phù hợp. "
            "Giữ giọng bình tĩnh, ngắn, không dài dòng hỏi phụ.\n"
            "Bắt buộc: Trả lời bằng tiếng Việt có dấu."
        )
    if intent == INTENT_SUMMARY:
        return (
            "Ý định: summary — Dùng hồ sơ và check-in được cung cấp để tóm tắt 5–7 ý, dễ hiểu, gợi ý bước tiếp theo. "
            "Không bịa số liệu không có trong ngữ cảnh.\n"
            "Bắt buộc: Trả lời bằng tiếng Việt có dấu."
        )
    if intent == INTENT_OUT_OF_SCOPE:
        return (
            "Ý định: out_of_scope — Từ chối nhẹ: bot chỉ hỗ trợ wellness, sàng lọc triệu chứng, và thông tin đặt lịch demo. "
            "Không kê đơn, không chẩn đoán chắc, không tư vấn nguy hiểm. Gợi ý kênh phù hợp (bác sĩ / cấp cứu).\n"
            "Bắt buộc: Trả lời bằng tiếng Việt có dấu."
        )
    return ""
