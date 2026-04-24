from __future__ import annotations

import asyncio
from pathlib import Path

import httpx

from app.core.config import settings
from app.services.examples_service import format_examples_for_prompt, load_few_shot_examples


class LlmError(RuntimeError):
    pass


def _assistant_text_from_openrouter(data: dict) -> str:
    """Lay noi dung assistant; mot so provider tra `content` la list cac block {type,text}."""
    try:
        msg = data["choices"][0]["message"]
    except (KeyError, IndexError, TypeError) as e:
        raise LlmError("Phan hoi OpenRouter khong co choices/message.") from e
    content = msg.get("content")
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                t = block.get("text")
                if isinstance(t, str) and t.strip():
                    parts.append(t.strip())
        return "\n".join(parts).strip()
    if content is None and isinstance(msg.get("refusal"), str):
        return str(msg["refusal"]).strip()
    return ""


def _load_system_prompt() -> str:
    prompt_path = Path(__file__).resolve().parents[1] / "prompts" / "system_prompt.txt"
    return prompt_path.read_text(encoding="utf-8")


def _build_user_context(
    *,
    user_profile: dict,
    latest_checkin: dict | None,
    weekly_summary_text: str = "",
    include_profile: bool,
    conversation_history: list[dict[str, str]] | None = None,
) -> str:
    if not include_profile:
        has_prior = bool(_history_for_openrouter(conversation_history))
        if has_prior:
            return (
                "Ho so onboarding/check-in: (KHONG gui day du trong luot nay).\n"
                "Phia tren da co cac luot user/assistant trong cung cuoc tro chuyen. "
                "Neu tin nhan HIEN TAI ngan hoac thieu ngu canh (vi du: 'phan nao quan trong nhat', "
                "'no la gi', 'tom tat lai', 'di kham som hay theo doi') thi BAN BAT BUOC dung thong tin "
                "tu cac luot TRUOC (dac biet ban assistant gan nhat: bang chi so, ket luan da neu).\n"
                "TUYET DOI khong noi kieu 'tin nhan khong de cap xet nghiem', 'khong co du lieu', "
                "'khong doc duoc anh' neu luot truoc da trinh bay ro bang/ket qua.\n"
                "Khong tu bo sung tuoi/can nang/check-in neu user chua nhac trong hoi thoai."
            )
        return (
            "Ho so ca nhan: (khong dinh kem cho luot nay — chi tra loi theo tin nhan hien tai, "
            "khong tu suy doan tuoi/gioi/check-in tru khi nguoi dung da noi trong tin nhan)."
        )
    parts: list[str] = []
    parts.append("Ho so nguoi dung (onboarding):")
    parts.append(
        f"- tuoi: {user_profile.get('age')}\n"
        f"- gioi tinh: {user_profile.get('gender')}\n"
        f"- chieu cao (cm): {user_profile.get('height_cm')}\n"
        f"- can nang (kg): {user_profile.get('weight_kg')}\n"
        f"- muc tieu: {user_profile.get('goal')}\n"
        f"- ghi chu y te: {user_profile.get('medical_notes') or '(khong)'}"
    )
    if latest_checkin:
        parts.append("\nCheck-in gan nhat:")
        parts.append(
            f"- ngu (gio): {latest_checkin.get('sleep_hours')}\n"
            f"- nuoc (lit): {latest_checkin.get('water_liters')}\n"
            f"- buoc: {latest_checkin.get('steps')}\n"
            f"- mood: {latest_checkin.get('mood')}\n"
            f"- trieu chung: {latest_checkin.get('symptoms') or '(khong)'}"
        )
    else:
        parts.append("\nCheck-in gan nhat: (chua co)")

    if weekly_summary_text and weekly_summary_text.strip():
        parts.append("\nWeekly-summary (7 ngay gan nhat):")
        parts.append(weekly_summary_text.strip())
    return "\n".join(parts).strip()


def _history_for_openrouter(conversation_history: list[dict[str, str]] | None) -> list[dict[str, str]]:
    if not conversation_history:
        return []
    return conversation_history[-20:]


async def chat_completion(
    *,
    user_profile: dict,
    latest_checkin: dict | None,
    weekly_summary_text: str = "",
    message: str,
    intent_addon: str = "",
    include_profile: bool = True,
    include_few_shot_examples: bool = True,
    media_attachments: list[dict] | None = None,
    conversation_history: list[dict[str, str]] | None = None,
) -> str:
    if not settings.openrouter_api_key:
        raise LlmError("Thieu OPENROUTER_API_KEY. Hay cau hinh bien moi truong truoc khi demo.")

    base_url = settings.openrouter_base_url.rstrip("/")
    url = f"{base_url}/chat/completions"

    system_prompt = _load_system_prompt()
    user_context = _build_user_context(
        user_profile=user_profile,
        latest_checkin=latest_checkin,
        weekly_summary_text=weekly_summary_text,
        include_profile=include_profile,
        conversation_history=conversation_history,
    )
    examples_text = ""
    if include_few_shot_examples:
        examples_text = format_examples_for_prompt(
            load_few_shot_examples(settings.triage_examples_path, limit=settings.triage_examples_limit)
        )

    system_parts = [
        system_prompt,
        "Bắt buộc: Luôn trả lời bằng tiếng Việt có dấu, tự nhiên.",
    ]
    if intent_addon.strip():
        system_parts.append(intent_addon.strip())
    if examples_text:
        system_parts.append(examples_text)

    # Nếu có gắn file media, chuyển sang dùng model hỗ trợ vision/multimodal.
    model_to_use = settings.openrouter_model or "openrouter/free"
    if media_attachments and settings.openrouter_multimodal_model:
        model_to_use = settings.openrouter_multimodal_model

    # Xây dựng nội dung cho role 'user'
    user_message_text = f"{user_context}\n\nTin nhan hien tai tu nguoi dung:\n{message}"
    
    if media_attachments:
        user_content = [{"type": "text", "text": user_message_text}] + media_attachments
    else:
        user_content = user_message_text

    history = _history_for_openrouter(conversation_history)
    messages_payload: list[dict] = [
        {
            "role": "system",
            "content": "\n\n".join(system_parts),
        },
    ]
    for turn in history:
        messages_payload.append({"role": turn["role"], "content": turn["content"]})
    messages_payload.append({"role": "user", "content": user_content})

    max_out = 2048 if media_attachments else 400

    payload = {
        "model": model_to_use,
        "messages": messages_payload,
        "temperature": 0.35 if media_attachments else 0.6,
        "max_tokens": max_out,
    }

    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
    }

    timeout = httpx.Timeout(settings.openrouter_timeout_s)

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = None
            # 429 từ model :free / upstream hay là tạm thời — thử lại vài lần trước khi báo lỗi.
            # 429 rate limit; 502/503/504 = provider/upstream tam thoi (vi du "no healthy upstream").
            for attempt in range(4):
                resp = await client.post(url, json=payload, headers=headers)
                if resp.status_code not in (429, 502, 503, 504):
                    break
                if attempt < 3:
                    await asyncio.sleep(2.0 * (attempt + 1))
    except httpx.TimeoutException as e:
        raise LlmError("OpenRouter bị timeout. Hãy thử lại sau ít phút.") from e
    except httpx.RequestError as e:
        raise LlmError("Không kết nối được OpenRouter. Kiểm tra mạng hoặc base URL.") from e

    assert resp is not None

    if resp.status_code == 401:
        raise LlmError("OpenRouter: API key khong hop le (401).")
    if resp.status_code == 402:
        raise LlmError("OpenRouter: hết quota hoặc cần thanh toán (402).")
    if resp.status_code == 429:
        hint = (
            "OpenRouter trả về 429 (rate limit — rất hay gặp với model miễn phí). "
            "Bạn có thể: đợi 1–2 phút rồi gửi lại; đổi sang model khác trên https://openrouter.ai/models "
            "(tìm vision/multimodal nếu gửi ảnh); đặt OPENROUTER_MULTIMODAL_MODEL riêng cho ảnh; "
            "hoặc nạp credit / gắn key Google riêng theo hướng dẫn OpenRouter để tăng hạn mức."
        )
        raise LlmError(f"{hint}\n\nChi tiết: {resp.text[:280]}")
    if resp.status_code in (502, 503, 504):
        hint = (
            f"OpenRouter trả về {resp.status_code} (lỗi tạm thời phía nhà cung cấp / upstream). "
            "Thông điệp kiểu **no healthy upstream** nghĩa là lúc đó không có máy chủ backend khỏe cho route model bạn chọn — "
            "thường do quá tải hoặc bảo trì, **không phải lỗi code app**. "
            "Đã thử gọi lại tự động vài lần; nếu vẫn lỗi: đợi vài phút, đổi sang model/provider khác trong `.env` (`OPENROUTER_MODEL` / `OPENROUTER_MULTIMODAL_MODEL`), "
            "hoặc thử `openrouter/free` để router chọn model còn sống."
        )
        raise LlmError(f"{hint}\n\nChi tiết: {resp.text[:280]}")
    if resp.status_code >= 400:
        raise LlmError(f"OpenRouter loi {resp.status_code}: {resp.text[:300]}")

    data = resp.json()
    try:
        return _assistant_text_from_openrouter(data)
    except LlmError:
        raise
    except Exception as e:  # noqa: BLE001
        raise LlmError("Phan hoi OpenRouter khong dung dinh dang mong doi.") from e
