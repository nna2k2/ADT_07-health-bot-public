from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Form, UploadFile, File
from fastapi.responses import HTMLResponse
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.db.models import Checkin, User, Reminder, Notification, Doctor, Appointment, FamilyMember
from app.db.session import get_db
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.checkins import CheckinIn, CheckinOut
from app.schemas.appointments import AppointmentCreate, AppointmentOut, DoctorOut
from app.schemas.notifications import NotificationCreate, NotificationOut
from app.schemas.reminders import ReminderCreate, ReminderOut, ReminderUpdate
from app.schemas.summaries import WeeklySummaryOut
from app.schemas.users import UserOnboardingIn, UserOut
from app.schemas.family_members import FamilyMemberCreate, FamilyMemberOut
from app.services.intent_service import (
    INTENT_BOOKING,
    INTENT_DOCTOR_AVAILABILITY,
    INTENT_EMERGENCY,
    INTENT_MEDICATION_REMINDER,
    INTENT_SYMPTOM_ADVICE,
    classify_intent,
    include_triage_in_prompt,
    intent_llm_addon,
    should_include_profile,
)
from app.services.llm_service import LlmError, chat_completion
from app.services.safety_service import check_safety, emergency_reply
from app.services.triage_fallback_reply import wellness_fallback_reply
from app.services.triage_service import TriageResult, triage_message
from app.services.file_parser import parse_files
from app.core.config import settings
from app.services.appointment_tokens import sign_token, verify_token
from app.services.email_service import send_email


def _coerce_chat_history(raw: list) -> list[dict[str, str]]:
    """Gioi han do dai va role hop le — tranh JSON bat ky lam payload LLM."""
    out: list[dict[str, str]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        role = item.get("role")
        content = item.get("content")
        if role not in ("user", "assistant") or not isinstance(content, str):
            continue
        c = content.strip()
        if not c:
            continue
        out.append({"role": role, "content": c[:12000]})
    return out[-24:]

def _contains_any(text: str, needles: list[str]) -> bool:
    t = (text or "").lower()
    return any(n.lower() in t for n in needles)


router = APIRouter()
_DEMO_DOCTOR_EMAIL = "anh252002@gmail.com"

# Seed + đồng bộ DB cũ: tên / chuyên khoa demo tiếng Việt
_DEMO_DOCTORS_SEED: list[tuple[str, str, str]] = [
    ("BS. Phạm Hoàng Long", "Nha khoa", "/assets/figma/Anh-bac-si-nam-2-min-e1718114189594.jpg"),
    ("BS. Trần Đức Anh", "Chuyên khoa Mắt", "/assets/figma/Anh-bac-si-nam-9-min.jpg"),
    ("BS. Nguyễn Thị Mai", "Ngoại khoa", "/assets/figma/Anh-profile-bac-si-nu-min-683x1024.jpg.webp"),
]
_DEMO_DOCTOR_LEGACY_NAMES: dict[str, tuple[str, str]] = {
    "Dr. Theresa Webb": ("BS. Phạm Hoàng Long", "Nha khoa"),
    "Dr. Cameron Williamson": ("BS. Trần Đức Anh", "Chuyên khoa Mắt"),
    "Dr. Guy Hawkins": ("BS. Nguyễn Thị Mai", "Ngoại khoa"),
}


def _triage_response_fields(triage: TriageResult) -> dict:
    return {
        "risk_level": triage.risk_level,
        "triage_score": triage.score,
        "suggested_actions": triage.suggested_actions,
        "possible_causes": triage.possible_causes,
        "follow_up_questions": triage.follow_up_questions,
        "reason_codes": triage.reason_codes,
        "rules_version": triage.rules_version,
    }


def _should_expose_triage_to_user(intent: str) -> bool:
    # Chỉ hiển thị “Mức độ: …” khi đang tư vấn/triage triệu chứng hoặc khẩn cấp.
    return intent in (INTENT_SYMPTOM_ADVICE, INTENT_EMERGENCY)


def _chat_cta_fields(intent: str) -> dict:
    if intent in (INTENT_BOOKING, INTENT_DOCTOR_AVAILABILITY):
        return {
            "cta_label": "Đặt lịch trong app",
            "cta_path": "/doctors",
        }
    if intent == INTENT_MEDICATION_REMINDER:
        return {
            "cta_label": "Tạo nhắc uống thuốc",
            "cta_path": "/reminders/new",
        }
    return {"cta_label": None, "cta_path": None}

def _weekly_summary_stats_text_for_prompt(*, user_id: str, db: Session) -> str:
    # SQLite stores naive timestamps; dùng UTC-naive phạm vi 7 ngày
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    from_dt = now - timedelta(days=7)
    stmt = (
        select(Checkin)
        .where(Checkin.user_id == user_id)
        .where(Checkin.created_at >= from_dt)
        .order_by(desc(Checkin.created_at))
    )
    checkins = list(db.execute(stmt).scalars().all())

    if not checkins:
        return "[Weekly-summary 7 ngày gần nhất] Chưa có check-in trong 7 ngày gần đây."

    checkin_days = len({c.created_at.date() for c in checkins})
    avg_sleep = sum(c.sleep_hours for c in checkins) / len(checkins)
    avg_water = sum(c.water_liters for c in checkins) / len(checkins)
    avg_steps = sum(c.steps for c in checkins) / len(checkins)

    from_d = from_dt.date() if isinstance(from_dt, datetime) else date.today()
    to_d = now.date() if isinstance(now, datetime) else date.today()
    avg_sleep_r = round(avg_sleep, 2)
    avg_water_r = round(avg_water, 2)
    avg_steps_r = round(avg_steps, 2)
    return (
        "[Thống kê check-in 7 ngày gần nhất — chỉ số trung bình, không phải chẩn đoán]\n"
        f"Khoảng thời gian: {from_d} → {to_d}\n"
        f"Số ngày có check-in: {checkin_days}\n"
        f"Ngủ trung bình: {avg_sleep_r} giờ/đêm\n"
        f"Nước uống trung bình: {avg_water_r} lít/ngày\n"
        f"Bước chân trung bình: {avg_steps_r:.0f} bước/ngày"
    )


def _appointment_response_page(*, heading: str, message: str, status: str, patient_name: str = "", patient_email: str = "", patient_phone: str = "", doctor_name: str = "", date_str: str = "", time_str: str = "", show_actions: bool = False, confirm_url: str = "", decline_url: str = "") -> str:
    badge_bg = {
        "pending": "#fff7ed",
        "confirmed": "#ecfdf3",
        "declined": "#fef2f2",
        "error": "#f5f5f5",
    }.get(status, "#f5f5f5")
    badge_fg = {
        "pending": "#c2410c",
        "confirmed": "#15803d",
        "declined": "#b91c1c",
        "error": "#525252",
    }.get(status, "#525252")
    actions_html = ""
    if show_actions:
        actions_html = f"""
        <div class="actions">
          <a class="btn btn--confirm" href="{confirm_url}">Xác nhận lịch hẹn</a>
          <a class="btn btn--decline" href="{decline_url}">Từ chối</a>
        </div>
        """

    return f"""<!doctype html>
<html lang="vi">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Xác nhận lịch hẹn</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f4f4f4;
      --card: #ffffff;
      --text: #171717;
      --muted: #737373;
      --green: #00a63e;
      --green-dark: #008a34;
      --red: #dc2626;
      --shadow: 0px 12px 40px rgba(0,0,0,0.10);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Roboto, Arial, sans-serif;
      background: radial-gradient(circle at top, #ffffff 0%, var(--bg) 50%, #ececec 100%);
      color: var(--text);
      min-height: 100vh;
      display: grid;
      place-items: center;
      padding: 24px;
    }}
    .card {{
      width: min(100%, 560px);
      background: var(--card);
      border-radius: 28px;
      box-shadow: var(--shadow);
      padding: 28px;
    }}
    .eyebrow {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      border-radius: 999px;
      padding: 8px 14px;
      background: {badge_bg};
      color: {badge_fg};
      font-size: 13px;
      font-weight: 700;
      margin-bottom: 14px;
    }}
    h1 {{
      margin: 0 0 8px;
      font-size: 28px;
      line-height: 34px;
    }}
    p {{
      margin: 0;
      color: var(--muted);
      line-height: 24px;
      font-size: 15px;
    }}
    .details {{
      margin-top: 22px;
      background: #fafafa;
      border-radius: 20px;
      padding: 18px;
      display: grid;
      gap: 12px;
    }}
    .row {{
      display: flex;
      align-items: flex-start;
      gap: 16px;
      border-bottom: 1px solid rgba(0,0,0,0.05);
      padding-bottom: 10px;
    }}
    .row:last-child {{
      border-bottom: none;
      padding-bottom: 0;
    }}
    .label {{
      color: var(--muted);
      font-size: 13px;
      width: 120px;
      flex: 0 0 120px;
    }}
    .value {{
      font-weight: 600;
      flex: 1;
      text-align: right;
      word-break: break-word;
    }}
    .actions {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
      margin-top: 22px;
    }}
    .btn {{
      text-align: center;
      text-decoration: none;
      border-radius: 999px;
      padding: 14px 18px;
      font-weight: 700;
      font-size: 14px;
    }}
    .btn--confirm {{
      background: var(--green);
      color: white;
    }}
    .btn--confirm:hover {{
      background: var(--green-dark);
    }}
    .btn--decline {{
      background: #fff1f2;
      color: var(--red);
    }}
    .foot {{
      margin-top: 18px;
      font-size: 12px;
      color: var(--muted);
      text-align: center;
    }}
  </style>
</head>
<body>
  <main class="card">
    <div class="eyebrow">{status.upper()}</div>
    <h1>{heading}</h1>
    <p>{message}</p>
    <section class="details">
      <div class="row"><div class="label">Bệnh nhân</div><div class="value">{patient_name or '-'}</div></div>
      <div class="row"><div class="label">Email</div><div class="value">{patient_email or '-'}</div></div>
      <div class="row"><div class="label">Số điện thoại</div><div class="value">{patient_phone or '-'}</div></div>
      <div class="row"><div class="label">Bác sĩ</div><div class="value">{doctor_name or '-'}</div></div>
      <div class="row"><div class="label">Ngày</div><div class="value">{date_str or '-'}</div></div>
      <div class="row"><div class="label">Giờ</div><div class="value">{time_str or '-'}</div></div>
    </section>
    {actions_html}
    <div class="foot">Health Care Bot Booking</div>
  </main>
</body>
</html>"""


@router.post("/users/onboarding", response_model=UserOut)
def user_onboarding(payload: UserOnboardingIn, db: Session = Depends(get_db)) -> UserOut:
    existing = db.get(User, payload.user_id)
    if existing:
        existing.age = payload.age
        existing.gender = payload.gender
        existing.height_cm = payload.height_cm
        existing.weight_kg = payload.weight_kg
        existing.goal = payload.goal
        existing.medical_notes = payload.medical_notes
        db.add(existing)
        db.commit()
        db.refresh(existing)
        return UserOut(
            user_id=existing.user_id,
            age=existing.age,
            gender=existing.gender,
            height_cm=existing.height_cm,
            weight_kg=existing.weight_kg,
            goal=existing.goal,
            medical_notes=existing.medical_notes,
        )

    user = User(
        user_id=payload.user_id,
        age=payload.age,
        gender=payload.gender,
        height_cm=payload.height_cm,
        weight_kg=payload.weight_kg,
        goal=payload.goal,
        medical_notes=payload.medical_notes,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return UserOut(
        user_id=user.user_id,
        age=user.age,
        gender=user.gender,
        height_cm=user.height_cm,
        weight_kg=user.weight_kg,
        goal=user.goal,
        medical_notes=user.medical_notes,
    )


@router.get("/users/{user_id}", response_model=UserOut)
def get_user(user_id: str, db: Session = Depends(get_db)) -> UserOut:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy user.")
    return UserOut(
        user_id=user.user_id,
        age=user.age,
        gender=user.gender,
        height_cm=user.height_cm,
        weight_kg=user.weight_kg,
        goal=user.goal,
        medical_notes=user.medical_notes,
    )


@router.get("/users/{user_id}/family-members", response_model=list[FamilyMemberOut])
def list_family_members(user_id: str, db: Session = Depends(get_db)) -> list[FamilyMemberOut]:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy user.")
    stmt = select(FamilyMember).where(FamilyMember.owner_user_id == user_id).order_by(FamilyMember.created_at)
    return list(db.execute(stmt).scalars().all())


@router.get("/family-members/{member_id}", response_model=FamilyMemberOut)
def get_family_member(member_id: int, db: Session = Depends(get_db)) -> FamilyMemberOut:
    item = db.get(FamilyMember, member_id)
    if not item:
        raise HTTPException(status_code=404, detail="Không tìm thấy thành viên.")
    return item


@router.post("/users/{user_id}/family-members", response_model=FamilyMemberOut)
def create_family_member(user_id: str, payload: FamilyMemberCreate, db: Session = Depends(get_db)) -> FamilyMemberOut:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy user.")
    item = FamilyMember(
        owner_user_id=user_id,
        member_user_id="",
        name=payload.name,
        relation=payload.relation,
        age=payload.age,
        gender=payload.gender,
        height_cm=payload.height_cm,
        weight_kg=payload.weight_kg,
        goal=payload.goal,
        medical_notes=payload.medical_notes,
        tracking_note=payload.tracking_note,
        avatar_bg=payload.avatar_bg,
        facts_text=payload.facts_text,
    )
    db.add(item)
    db.flush()  # get item.id

    # Create a synthetic user profile for this member so bot/checkin/summary work "như onboarding".
    member_uid = f"{user_id}__m{item.id}"
    item.member_user_id = member_uid
    # Ensure users row exists (rare race if retried)
    existing_member_user = db.get(User, member_uid)
    if not existing_member_user:
        db.add(
            User(
                user_id=member_uid,
                age=payload.age,
                gender=payload.gender,
                height_cm=payload.height_cm,
                weight_kg=payload.weight_kg,
                goal=payload.goal,
                medical_notes=payload.medical_notes,
            )
        )
    db.commit()
    db.refresh(item)
    return item


@router.delete("/family-members/{member_id}")
def delete_family_member(member_id: int, db: Session = Depends(get_db)) -> dict:
    item = db.get(FamilyMember, member_id)
    if not item:
        raise HTTPException(status_code=404, detail="Không tìm thấy thành viên.")
    member_uid = (item.member_user_id or "").strip()
    if member_uid:
        # delete checkins belonging to member profile
        db.query(Checkin).filter(Checkin.user_id == member_uid).delete()
        u = db.get(User, member_uid)
        if u:
            db.delete(u)
    db.delete(item)
    db.commit()
    return {"detail": "ok", "deleted_id": member_id}


@router.post("/checkins", response_model=CheckinOut)
def create_checkin(payload: CheckinIn, db: Session = Depends(get_db)) -> CheckinOut:
    user = db.get(User, payload.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy user. Hãy onboarding trước.")

    ck = Checkin(
        user_id=payload.user_id,
        sleep_hours=payload.sleep_hours,
        water_liters=payload.water_liters,
        steps=payload.steps,
        mood=payload.mood,
        symptoms=payload.symptoms,
    )
    db.add(ck)
    db.commit()
    db.refresh(ck)
    return CheckinOut(
        id=ck.id,
        user_id=ck.user_id,
        sleep_hours=ck.sleep_hours,
        water_liters=ck.water_liters,
        steps=ck.steps,
        mood=ck.mood,
        symptoms=ck.symptoms,
        created_at=ck.created_at,
    )


@router.post("/chat", response_model=ChatResponse)
async def chat(
    user_id: str = Form(...),
    message: str = Form(...),
    files: list[UploadFile] = File(default=[]),
    conversation_json: str | None = Form(default=None),
    db: Session = Depends(get_db)
) -> ChatResponse:
    safe, keyword = check_safety(message)
    if not safe:
        triage = triage_message(message)
        triage_fields = _triage_response_fields(triage) if _should_expose_triage_to_user(INTENT_EMERGENCY) else {}
        return ChatResponse(
            reply=emergency_reply(keyword),
            intent=INTENT_EMERGENCY,
            blocked=True,
            reason="safety_keyword",
            **triage_fields,
        )

    user = db.get(User, user_id)
    if not user:
        # Cho phép hỏi bot để "xem đã có hồ sơ chưa" thay vì trả 404.
        # (Vẫn chặn các trường hợp khẩn cấp ở nhánh safety phía trên.)
        triage = triage_message(message)
        # Thiếu hồ sơ: vẫn không hiển thị “Mức độ” vì chưa phải tư vấn triệu chứng.
        return ChatResponse(
            reply=(
                "Mình **chưa thấy hồ sơ (onboarding)** của bạn trong hệ thống.\n\n"
                "Bạn hãy vào màn **Tạo hồ sơ** để nhập tuổi/giới tính/chiều cao/cân nặng/mục tiêu trước, "
                "sau đó mình sẽ dùng hồ sơ + check-in để tư vấn wellness sát với bạn hơn.\n\n"
                "Lưu ý: Mình là bot wellness, không chẩn đoán bệnh hay thay thế bác sĩ."
            ),
            intent=INTENT_SUMMARY,
            blocked=False,
            reason="missing_user_profile",
            cta_label="Tạo hồ sơ",
            cta_path="/onboarding",
        )

    extracted_text, media_attachments = parse_files(files)

    conversation_history: list[dict[str, str]] = []
    if conversation_json and conversation_json.strip():
        try:
            parsed = json.loads(conversation_json)
            if isinstance(parsed, list):
                conversation_history = _coerce_chat_history(parsed)
        except json.JSONDecodeError:
            conversation_history = []

    triage = triage_message(message)
    intent = classify_intent(
        message,
        triage,
        media_attachments=media_attachments,
        conversation_history=conversation_history,
    )
    triage_fields = _triage_response_fields(triage) if _should_expose_triage_to_user(intent) else {}

    stmt = select(Checkin).where(Checkin.user_id == user_id).order_by(desc(Checkin.created_at)).limit(1)
    latest_ck = db.execute(stmt).scalars().first()
    weekly_summary_text = _weekly_summary_stats_text_for_prompt(user_id=user_id, db=db)

    # Trả lời trực tiếp cho câu hỏi "triệu chứng tôi đã điền/check-in có chưa?"
    # để tránh phụ thuộc vào LLM trong các câu hỏi trạng thái dữ liệu.
    if _contains_any(message, ["triệu chứng", "trieu chung"]) and _contains_any(
        message,
        [
            "da dien",
            "đã điền",
            "check-in",
            "check in",
            "checkin",
            "hom nay",
            "hôm nay",
            "có chưa",
            "chua",
            "chưa",
        ],
    ):
        triage = triage_message(message)
        triage_fields = _triage_response_fields(triage) if _should_expose_triage_to_user(intent) else {}
        if latest_ck and (latest_ck.symptoms or "").strip():
            sym = latest_ck.symptoms.strip()
            when = latest_ck.created_at.isoformat() if isinstance(latest_ck.created_at, datetime) else ""
            when_line = f"(Thời điểm lưu: {when})\n\n" if when else ""
            return ChatResponse(
                reply=(
                    f"Mình thấy **triệu chứng bạn đã check-in gần nhất** là:\n\n"
                    f"- {sym}\n\n"
                    f"{when_line}"
                    "Nếu bạn muốn, bạn mô tả thêm mức độ (nhẹ/vừa/nặng) và thời gian kéo dài để mình gợi ý wellness phù hợp."
                ),
                intent=INTENT_SUMMARY,
                blocked=False,
                reason="echo_latest_checkin_symptoms",
                **triage_fields,
            )
        return ChatResponse(
            reply=(
                "Mình **chưa thấy triệu chứng nào được lưu** trong check-in gần đây.\n\n"
                "Bạn có thể vào màn **Daily check-in** và nhập ô **Triệu chứng**, sau đó bấm **Lưu check-in**."
            ),
            intent=INTENT_SUMMARY,
            blocked=False,
            reason="missing_latest_checkin_symptoms",
            cta_label="Daily check-in",
            cta_path="/checkin",
            **triage_fields,
        )

    user_profile = {
        "user_id": user.user_id,
        "age": user.age,
        "gender": user.gender,
        "height_cm": user.height_cm,
        "weight_kg": user.weight_kg,
        "goal": user.goal,
        "medical_notes": user.medical_notes,
    }
    latest_checkin = None
    if latest_ck:
        latest_checkin = {
            "sleep_hours": latest_ck.sleep_hours,
            "water_liters": latest_ck.water_liters,
            "steps": latest_ck.steps,
            "mood": latest_ck.mood,
            "symptoms": latest_ck.symptoms,
            "created_at": latest_ck.created_at.isoformat() if isinstance(latest_ck.created_at, datetime) else None,
        }

    try:
        combo_message = message
        if extracted_text:
            combo_message = f"{message}\n\nNội dung file đính kèm:\n{extracted_text}".strip()

        # Luôn chèn AI triage vào prompt (nội bộ) để LLM bám mức độ nghiêm trọng nhất quán,
        # nhưng TUYỆT ĐỐI không được lộ risk_level/triage_score/reason_codes cho người dùng.
        triage_hint = (
            "KET QUA TRIAGE (noi bo — KHONG nhac risk_level/triage_score/reason_codes trong tra loi cho user):\n"
            f"- risk_level: {triage.risk_level}\n"
            f"- triage_score: {triage.score}\n"
            f"- suggested_actions: {triage.suggested_actions}\n"
            f"- follow_up_questions (long ghep tu nhien 1-2 cau): {triage.follow_up_questions}\n"
            f"- possible_causes (tham khao): {triage.possible_causes}\n"
            f"- reason_codes: {triage.reason_codes}"
        )
        llm_message = f"{triage_hint}\n\nUser message:\n{combo_message}"

        # Yêu cầu: hồ sơ + check-in luôn là dữ liệu đầu vào cho chatbot.
        include_profile = True
        intent_addon = intent_llm_addon(intent, triage, combo_message)
        use_examples = intent in (INTENT_SYMPTOM_ADVICE, INTENT_EMERGENCY)

        reply = await chat_completion(
            user_profile=user_profile,
            latest_checkin=latest_checkin,
            weekly_summary_text=weekly_summary_text,
            message=llm_message,
            intent_addon=intent_addon,
            include_profile=include_profile,
            include_few_shot_examples=use_examples,
            media_attachments=media_attachments,
            conversation_history=conversation_history,
        )
        if not reply.strip():
            has_lab_image = any(
                isinstance(m, dict) and m.get("type") == "image_url" for m in (media_attachments or [])
            )
            if has_lab_image:
                reply = (
                    "Mình **không nhận được** nội dung giải thích từ AI cho ảnh vừa gửi (model trả về rỗng hoặc không xử lý được ảnh).\n\n"
                    "**Bạn có thể thử:** (1) chụp lại ảnh sáng, thẳng, đủ cận từng dòng chỉ số; "
                    "(2) kiểm tra `OPENROUTER_MULTIMODAL_MODEL` và quota OpenRouter; "
                    "(3) gửi lại sau vài phút nếu gặp giới hạn API.\n\n"
                    "Nếu vẫn lỗi, hãy **chép tay** các chỉ số vào ô chat để mình hỗ trợ theo hướng wellness.\n\n"
                    "Đây không phải chẩn đoán và không thay thế bác sĩ."
                )
            else:
                reply = wellness_fallback_reply(triage, combo_message)
    except LlmError as e:
        extra_hint = ""
        if intent in (INTENT_BOOKING, INTENT_DOCTOR_AVAILABILITY):
            extra_hint = (
                "\n\nBạn vẫn có thể **đặt lịch demo trong app**: mở mục **Danh sách bác sĩ** hoặc **Đặt lịch** trên menu, "
                "chọn bác sĩ, ngày và giờ trống, điền họ tên / email / SĐT rồi gửi yêu cầu."
            )
        return ChatResponse(
            reply=(
                "Hiện tại mình chưa gọi được AI do lỗi cấu hình/quota/timeout.\n\n"
                f"Chi tiết: {str(e)}\n\n"
                "Trong lúc chờ, bạn có thể nói rõ hơn mục tiêu của bạn hôm nay (ngủ/nước/vận động/căng thẳng) để mình gợi ý theo hướng wellness."
                f"{extra_hint}"
            ),
            intent=intent,
            blocked=False,
            reason="llm_error",
            **triage_fields,
            **_chat_cta_fields(intent),
        )

    # Guardrail: chỉ thêm dòng disclaimer khi đã có nội dung thật (tránh chỉ còn mỗi “Lưu ý…”)
    if reply.strip():
        final_reply = (
            f"{reply.strip()}\n\n"
            "Lưu ý: Mình là bot wellness, không chẩn đoán bệnh hay thay thế bác sĩ."
        ).strip()
    else:
        final_reply = wellness_fallback_reply(triage, message)
    return ChatResponse(
        reply=final_reply,
        intent=intent,
        blocked=False,
        reason=None,
        **triage_fields,
        **_chat_cta_fields(intent),
    )


@router.get("/users/{user_id}/weekly-summary", response_model=WeeklySummaryOut)
def weekly_summary(user_id: str, db: Session = Depends(get_db)) -> WeeklySummaryOut:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy user.")

    # SQLite stores naive timestamps; dùng UTC-naive phạm vi 7 ngày
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    from_dt = now - timedelta(days=7)

    stmt = (
        select(Checkin)
        .where(Checkin.user_id == user_id)
        .where(Checkin.created_at >= from_dt)
        .order_by(desc(Checkin.created_at))
    )
    checkins = list(db.execute(stmt).scalars().all())

    checkin_days = len({c.created_at.date() for c in checkins})
    if checkins:
        avg_sleep = sum(c.sleep_hours for c in checkins) / len(checkins)
        avg_water = sum(c.water_liters for c in checkins) / len(checkins)
        avg_steps = sum(c.steps for c in checkins) / len(checkins)
    else:
        avg_sleep = 0.0
        avg_water = 0.0
        avg_steps = 0.0

    from_d = from_dt.date() if isinstance(from_dt, datetime) else date.today()
    to_d = now.date() if isinstance(now, datetime) else date.today()
    avg_sleep_r = round(avg_sleep, 2)
    avg_water_r = round(avg_water, 2)
    avg_steps_r = round(avg_steps, 2)
    stats_text = (
        "[Thống kê check-in 7 ngày gần nhất — chỉ số trung bình, không phải chẩn đoán]\n"
        f"Khoảng thời gian: {from_d} → {to_d}\n"
        f"Số ngày có check-in: {checkin_days}\n"
        f"Ngủ trung bình: {avg_sleep_r} giờ/đêm\n"
        f"Nước uống trung bình: {avg_water_r} lít/ngày\n"
        f"Bước chân trung bình: {avg_steps_r:.0f} bước/ngày"
    )

    return WeeklySummaryOut(
        user_id=user_id,
        from_date=from_d,
        to_date=to_d,
        checkin_days=checkin_days,
        avg_sleep_hours=avg_sleep_r,
        avg_water_liters=avg_water_r,
        avg_steps=avg_steps_r,
        stats_text=stats_text,
    )

# --- Reminders API ---

@router.get("/users/{user_id}/reminders", response_model=list[ReminderOut])
def get_reminders(user_id: str, db: Session = Depends(get_db)):
    reminders = db.query(Reminder).filter(Reminder.user_id == user_id).all()
    return reminders

@router.post("/users/{user_id}/reminders", response_model=ReminderOut)
def create_reminder(user_id: str, payload: ReminderCreate, db: Session = Depends(get_db)):
    new_reminder = Reminder(
        user_id=user_id,
        title=payload.title,
        description=payload.description,
        date_str=(payload.date_str or "").strip(),
        time_str=payload.time_str,
        type=payload.type,
        is_active=payload.is_active,
        one_shot=bool(getattr(payload, "one_shot", False)),
    )
    db.add(new_reminder)
    db.commit()
    db.refresh(new_reminder)
    return new_reminder

@router.put("/reminders/{reminder_id}", response_model=ReminderOut)
def update_reminder(reminder_id: int, payload: ReminderUpdate, db: Session = Depends(get_db)):
    reminder = db.get(Reminder, reminder_id)
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
    
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(reminder, key, value)
        
    db.commit()
    db.refresh(reminder)
    return reminder

@router.delete("/reminders/{reminder_id}")
def delete_reminder(reminder_id: int, db: Session = Depends(get_db)):
    reminder = db.get(Reminder, reminder_id)
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
    
    db.delete(reminder)
    db.commit()
    return {"detail": "Reminder deleted successfully"}


# --- Notifications API (persist to DB) ---

@router.get("/users/{user_id}/notifications", response_model=list[NotificationOut])
def get_notifications(user_id: str, db: Session = Depends(get_db)) -> list[NotificationOut]:
    stmt = select(Notification).where(Notification.user_id == user_id).order_by(desc(Notification.created_at)).limit(50)
    items = list(db.execute(stmt).scalars().all())
    return items


@router.post("/users/{user_id}/notifications", response_model=NotificationOut)
def create_notification(user_id: str, payload: NotificationCreate, db: Session = Depends(get_db)) -> NotificationOut:
    # ensure user exists (same behavior as other endpoints)
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy user. Hãy onboarding trước.")

    item = Notification(
        user_id=user_id,
        kind=payload.kind,
        title=payload.title,
        message=payload.message,
        read=payload.read,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.post("/users/{user_id}/notifications/mark-all-read")
def mark_all_notifications_read(user_id: str, db: Session = Depends(get_db)) -> dict:
    stmt = select(Notification).where(Notification.user_id == user_id).where(Notification.read == False)  # noqa: E712
    items = list(db.execute(stmt).scalars().all())
    for it in items:
        it.read = True
        db.add(it)
    db.commit()
    return {"detail": "ok", "updated": len(items)}


# --- Doctors / Appointments (booking flow) ---

@router.get("/doctors", response_model=list[DoctorOut])
def list_doctors(db: Session = Depends(get_db)) -> list[DoctorOut]:
    # Seed demo doctors if empty
    existing = list(db.execute(select(Doctor).order_by(Doctor.id)).scalars().all())
    if not existing:
        demo = [
            Doctor(name=name, specialty=spec, email=_DEMO_DOCTOR_EMAIL, avatar_url=avatar)
            for name, spec, avatar in _DEMO_DOCTORS_SEED
        ]
        for d in demo:
            db.add(d)
        db.commit()
        existing = list(db.execute(select(Doctor).order_by(Doctor.id)).scalars().all())
    else:
        # Nếu DB demo đã có quá nhiều bác sĩ (từ seed cũ), giữ đúng danh sách demo hiện tại.
        # Chỉ áp dụng khi tất cả đều dùng email demo (để tránh xóa dữ liệu "thật").
        seed_n = len(_DEMO_DOCTORS_SEED)
        if len(existing) != seed_n and all((d.email or "") == _DEMO_DOCTOR_EMAIL for d in existing):
            for d in existing:
                db.delete(d)
            db.commit()
            demo = [
                Doctor(name=name, specialty=spec, email=_DEMO_DOCTOR_EMAIL, avatar_url=avatar)
                for name, spec, avatar in _DEMO_DOCTORS_SEED
            ]
            for d in demo:
                db.add(d)
            db.commit()
            return list(db.execute(select(Doctor).order_by(Doctor.id)).scalars().all())

        changed = False
        seed_by_name = {name: (spec, avatar) for name, spec, avatar in _DEMO_DOCTORS_SEED}
        for d in existing:
            if d.email != _DEMO_DOCTOR_EMAIL:
                d.email = _DEMO_DOCTOR_EMAIL
                db.add(d)
                changed = True
            seed = seed_by_name.get(d.name.strip())
            if seed:
                spec, avatar = seed
                if d.specialty != spec or (d.avatar_url or "") != avatar:
                    d.specialty = spec
                    d.avatar_url = avatar
                    db.add(d)
                    changed = True
            legacy = _DEMO_DOCTOR_LEGACY_NAMES.get(d.name.strip())
            if legacy:
                new_name, new_spec = legacy
                if d.name != new_name or d.specialty != new_spec:
                    d.name = new_name
                    d.specialty = new_spec
                    db.add(d)
                    changed = True
        if changed:
            db.commit()
            existing = list(db.execute(select(Doctor).order_by(Doctor.id)).scalars().all())
    return existing


@router.get("/doctors/{doctor_id}/slots")
def list_doctor_slots(doctor_id: int, date_str: str, db: Session = Depends(get_db)) -> dict:
    # Simple demo availability: fixed half-hour slots
    doctor = db.get(Doctor, doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    base_slots = [
        "09:00",
        "09:30",
        "10:00",
        "10:30",
        "14:00",
        "14:30",
        "15:00",
        "15:30",
    ]
    stmt = (
        select(Appointment)
        .where(Appointment.doctor_id == doctor_id)
        .where(Appointment.date_str == date_str)
        .where(Appointment.status.in_(["pending", "confirmed"]))
    )
    booked = {a.time_str for a in db.execute(stmt).scalars().all()}
    available = [t for t in base_slots if t not in booked]
    return {"doctor_id": doctor_id, "date_str": date_str, "slots": available}


@router.post("/appointments", response_model=AppointmentOut)
def create_appointment(payload: AppointmentCreate, db: Session = Depends(get_db)) -> AppointmentOut:
    user = db.get(User, payload.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy user. Hãy onboarding trước.")
    doctor = db.get(Doctor, payload.doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    # Prevent double booking
    stmt = (
        select(Appointment)
        .where(Appointment.doctor_id == payload.doctor_id)
        .where(Appointment.date_str == payload.date_str)
        .where(Appointment.time_str == payload.time_str)
        .where(Appointment.status.in_(["pending", "confirmed"]))
        .limit(1)
    )
    exists = db.execute(stmt).scalars().first()
    if exists:
        raise HTTPException(status_code=409, detail="Khung giờ này đã được đặt. Bạn chọn giờ khác nhé.")

    appt = Appointment(
        user_id=payload.user_id,
        doctor_id=payload.doctor_id,
        patient_name=payload.patient_name,
        patient_email=payload.patient_email,
        patient_phone=payload.patient_phone,
        note=payload.note,
        date_str=payload.date_str,
        time_str=payload.time_str,
        status="pending",
    )
    db.add(appt)
    db.commit()
    db.refresh(appt)

    # Use a single "view" token (doctor chooses confirm/decline on the page).
    view_token = sign_token({"appointment_id": appt.id}, secret=settings.appointment_token_secret)
    base = settings.public_base_url.rstrip("/")
    open_url = f"{base}/appointments/respond?token={view_token}"
    confirm_url = f"{base}/appointments/respond?token={view_token}&action=confirm"
    decline_url = f"{base}/appointments/respond?token={view_token}&action=decline"

    body = (
        f"Có lịch hẹn mới.\n\n"
        f"- Bệnh nhân: {payload.patient_name} ({payload.patient_email})\n"
        f"- Số điện thoại: {payload.patient_phone}\n"
        f"- Thời gian: {payload.date_str} {payload.time_str}\n"
        f"- Ghi chú: {payload.note or 'Không có'}\n\n"
        f"Mở yêu cầu lịch hẹn: {open_url}\n"
    ).strip()
    body_html = f"""<!doctype html>
<html lang="vi">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Yêu cầu đặt lịch khám</title>
</head>
<body style="margin:0;padding:24px;background:#f4f4f4;font-family:Roboto,Arial,sans-serif;color:#171717;">
  <div style="max-width:560px;margin:0 auto;background:#ffffff;border-radius:24px;padding:28px;box-shadow:0 12px 40px rgba(0,0,0,0.08);">
    <div style="display:inline-block;padding:8px 14px;border-radius:999px;background:#fff7ed;color:#c2410c;font-size:13px;font-weight:700;">PENDING</div>
    <h1 style="margin:16px 0 8px;font-size:28px;line-height:34px;">Yêu cầu xác nhận lịch hẹn</h1>
    <p style="margin:0;color:#737373;font-size:15px;line-height:24px;">Bạn có một yêu cầu đặt lịch mới. Nhấn nút bên dưới để mở trang xác nhận lịch hẹn.</p>

    <div style="margin-top:22px;background:#fafafa;border-radius:20px;padding:18px;">
      <div style="display:flex;align-items:flex-start;gap:16px;border-bottom:1px solid rgba(0,0,0,0.05);padding-bottom:10px;margin-bottom:10px;"><span style="color:#737373;font-size:13px;width:120px;flex:0 0 120px;">Bệnh nhân</span><strong style="flex:1;text-align:right;word-break:break-word;">{payload.patient_name}</strong></div>
      <div style="display:flex;align-items:flex-start;gap:16px;border-bottom:1px solid rgba(0,0,0,0.05);padding-bottom:10px;margin-bottom:10px;"><span style="color:#737373;font-size:13px;width:120px;flex:0 0 120px;">Email</span><strong style="flex:1;text-align:right;word-break:break-word;">{payload.patient_email}</strong></div>
      <div style="display:flex;align-items:flex-start;gap:16px;border-bottom:1px solid rgba(0,0,0,0.05);padding-bottom:10px;margin-bottom:10px;"><span style="color:#737373;font-size:13px;width:120px;flex:0 0 120px;">Số điện thoại</span><strong style="flex:1;text-align:right;word-break:break-word;">{payload.patient_phone}</strong></div>
      <div style="display:flex;align-items:flex-start;gap:16px;border-bottom:1px solid rgba(0,0,0,0.05);padding-bottom:10px;margin-bottom:10px;"><span style="color:#737373;font-size:13px;width:120px;flex:0 0 120px;">Ngày</span><strong style="flex:1;text-align:right;word-break:break-word;">{payload.date_str}</strong></div>
      <div style="display:flex;align-items:flex-start;gap:16px;border-bottom:1px solid rgba(0,0,0,0.05);padding-bottom:10px;margin-bottom:10px;"><span style="color:#737373;font-size:13px;width:120px;flex:0 0 120px;">Giờ</span><strong style="flex:1;text-align:right;word-break:break-word;">{payload.time_str}</strong></div>
      <div style="display:flex;align-items:flex-start;gap:16px;"><span style="color:#737373;font-size:13px;width:120px;flex:0 0 120px;">Ghi chú</span><strong style="flex:1;text-align:right;word-break:break-word;">{payload.note or 'Không có'}</strong></div>
    </div>

    <div style="margin-top:22px;">
      <a href="{open_url}" style="display:block;text-align:center;text-decoration:none;border-radius:999px;padding:14px 18px;background:#00a63e;color:#ffffff;font-weight:700;font-size:14px;">Mở yêu cầu lịch hẹn</a>
    </div>

    <p style="margin:18px 0 0;text-align:center;font-size:12px;color:#737373;">Health Care Bot Booking</p>
  </div>
</body>
</html>"""
    send_email(
        to_email=doctor.email,
        subject="Yêu cầu đặt lịch khám (cần xác nhận)",
        body_text=body,
        body_html=body_html,
    )

    return appt


@router.get("/users/{user_id}/appointments", response_model=list[AppointmentOut])
def list_user_appointments(user_id: str, db: Session = Depends(get_db)) -> list[AppointmentOut]:
    stmt = select(Appointment).where(Appointment.user_id == user_id).order_by(desc(Appointment.created_at)).limit(50)
    return list(db.execute(stmt).scalars().all())


@router.get("/appointments/respond", response_class=HTMLResponse)
def respond_appointment(token: str, action: str | None = None, db: Session = Depends(get_db)) -> HTMLResponse:
    try:
        payload = verify_token(token, secret=settings.appointment_token_secret)
    except Exception:
        html = _appointment_response_page(
            heading="Liên kết không hợp lệ",
            message="Liên kết xác nhận hoặc từ chối này đã hết hạn hoặc không đúng.",
            status="error",
        )
        return HTMLResponse(content=html, status_code=400)

    appt_id = int(payload.get("appointment_id", 0) or 0)
    chosen_action = (action or "").strip().lower()
    if not appt_id:
        html = _appointment_response_page(
            heading="Liên kết không hợp lệ",
            message="Không thể đọc yêu cầu lịch hẹn từ liên kết này.",
            status="error",
        )
        return HTMLResponse(content=html, status_code=400)

    appt = db.get(Appointment, appt_id)
    if not appt:
        html = _appointment_response_page(
            heading="Không tìm thấy lịch hẹn",
            message="Lịch hẹn này không tồn tại hoặc đã bị xóa.",
            status="error",
        )
        return HTMLResponse(content=html, status_code=404)

    doctor = db.get(Doctor, appt.doctor_id)
    doctor_name = doctor.name if doctor else "Bác sĩ"

    if appt.status in ("confirmed", "declined"):
        heading = "Lịch hẹn đã được xử lý"
        message = "Bạn đã phản hồi lịch hẹn này trước đó."
        html = _appointment_response_page(
            heading=heading,
            message=message,
            status=appt.status,
            patient_name=appt.patient_name,
            patient_email=appt.patient_email,
            patient_phone=appt.patient_phone,
            doctor_name=doctor_name,
            date_str=appt.date_str,
            time_str=appt.time_str,
        )
        return HTMLResponse(content=html)

    if not chosen_action:
        base = settings.public_base_url.rstrip("/")
        confirm_url = f"{base}/appointments/respond?token={token}&action=confirm"
        decline_url = f"{base}/appointments/respond?token={token}&action=decline"
        heading = "Yêu cầu xác nhận lịch hẹn"
        message = "Vui lòng xem thông tin bên dưới và chọn xác nhận hoặc từ chối."
        html = _appointment_response_page(
            heading=heading,
            message=message,
            status="pending",
            patient_name=appt.patient_name,
            patient_email=appt.patient_email,
            patient_phone=appt.patient_phone,
            doctor_name=doctor_name,
            date_str=appt.date_str,
            time_str=appt.time_str,
            show_actions=True,
            confirm_url=confirm_url,
            decline_url=decline_url,
        )
        return HTMLResponse(content=html)

    if chosen_action not in ("confirm", "decline"):
        html = _appointment_response_page(
            heading="Hành động không hợp lệ",
            message="Hành động không hợp lệ. Vui lòng thử lại.",
            status="error",
            patient_name=appt.patient_name,
            patient_email=appt.patient_email,
            patient_phone=appt.patient_phone,
            doctor_name=doctor_name,
            date_str=appt.date_str,
            time_str=appt.time_str,
        )
        return HTMLResponse(content=html, status_code=400)

    if chosen_action == "confirm":
        appt.status = "confirmed"
        title = "Lịch hẹn đã xác nhận"
        msg = f"{doctor_name} đã xác nhận lịch {appt.date_str} lúc {appt.time_str}."
        heading = "Đã xác nhận lịch hẹn"
        message = "Lịch hẹn đã được xác nhận thành công và thông báo đã gửi cho người dùng."
    else:
        appt.status = "declined"
        title = "Lịch hẹn bị từ chối"
        msg = f"{doctor_name} đã từ chối lịch {appt.date_str} lúc {appt.time_str}. Bạn vui lòng chọn giờ khác."
        heading = "Đã từ chối lịch hẹn"
        message = "Hệ thống đã thông báo cho người dùng để chọn một khung giờ khác."

    db.add(appt)
    db.add(
        Notification(
            user_id=appt.user_id,
            kind="appointment",
            title=title,
            message=msg,
            read=False,
        )
    )
    if chosen_action == "confirm":
        # Auto-create a one-shot reminder at the appointment time.
        db.add(
            Reminder(
                user_id=appt.user_id,
                title=f"Lịch hẹn: {doctor_name}",
                description=f"Bạn có lịch hẹn {appt.date_str} lúc {appt.time_str}.",
                date_str=appt.date_str,
                time_str=appt.time_str,
                type="appointment",
                is_active=True,
                one_shot=True,
            )
        )
    db.commit()
    db.refresh(appt)
    html = _appointment_response_page(
        heading=heading,
        message=message,
        status=appt.status,
        patient_name=appt.patient_name,
        patient_email=appt.patient_email,
        patient_phone=appt.patient_phone,
        doctor_name=doctor_name,
        date_str=appt.date_str,
        time_str=appt.time_str,
    )
    return HTMLResponse(content=html)
