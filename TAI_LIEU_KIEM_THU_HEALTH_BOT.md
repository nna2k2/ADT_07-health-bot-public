# Tài liệu kiểm thử — Health Care Bot MVP (Wellness)

Tài liệu này mô tả kế hoạch và checklist kiểm thử cho dự án `health-bot` (Angular frontend + FastAPI backend + SQLite + OpenRouter).

## 1) Mục tiêu

- Xác nhận các luồng demo chính hoạt động ổn định: **Splash → Onboarding → Dashboard → Check-in / Chat / Weekly summary / Profile / Booking / Notifications / Reminders**.
- Đảm bảo các ràng buộc an toàn: bot **không chẩn đoán**, có **safety guardrail** khi gặp tình huống khẩn cấp.
- Kiểm tra tích hợp API ↔ UI và các tình huống lỗi thường gặp (thiếu onboarding, lỗi AI quota/timeout, CORS, double booking).

## 2) Phạm vi

- **In-scope (cần kiểm thử)**
  - Backend API (FastAPI):
    - `GET /health`
    - `POST /users/onboarding`, `GET /users/{user_id}`
    - Family members: `GET /users/{user_id}/family-members`, `POST /users/{user_id}/family-members`, `GET /family-members/{member_id}`, `DELETE /family-members/{member_id}`
    - `POST /checkins`
    - `POST /chat` (multipart form: `user_id`, `message`, optional `conversation_json`, optional `files[]`)
    - `GET /users/{user_id}/weekly-summary`
    - Reminders: `GET /users/{user_id}/reminders`, `POST /users/{user_id}/reminders`, `PUT /reminders/{reminder_id}`, `DELETE /reminders/{reminder_id}`
    - Notifications: `GET /users/{user_id}/notifications`, `POST /users/{user_id}/notifications`, `POST /users/{user_id}/notifications/mark-all-read`
    - Doctors & booking:
      - `GET /doctors`
      - `GET /doctors/{doctor_id}/slots?date_str=YYYY-MM-DD`
      - `POST /appointments`
      - `GET /users/{user_id}/appointments`
      - `GET /appointments/respond?token=...&action=(confirm|decline)` (HTML response)
  - Frontend UI (Angular): Onboarding, Dashboard, Check-in, Chat, Doctors/Booking, Reminders, Notifications, Profile.

- **Out-of-scope (không bắt buộc cho MVP)**
  - Hiệu năng tải lớn/scale production.
  - Pentest chuyên sâu (chỉ kiểm tra bảo mật cơ bản).
  - Tính chính xác y khoa (chỉ kiểm tra theo tiêu chí “wellness + disclaimer + guardrail”).

## 3) Môi trường kiểm thử

### 3.0. Production / Deploy (bản chạy thật)

- Web (SPA): [https://www.healthbot1.work.gd/](https://www.healthbot1.work.gd/)
- API:
  - Nếu bạn deploy kiểu “cùng domain” (Nginx proxy): thường là `https://www.healthbot1.work.gd/api`
  - Nếu API là domain riêng: ghi rõ base URL API (ví dụ `https://api.healthbot1.work.gd`)

Ghi chú nhanh khi test production:
- Frontend production trong code đang theo hướng **`backendBaseUrl: '/api'`** (cùng domain). Vì vậy khi bạn mở web deploy, hãy kiểm tra DevTools → Network có gọi được `GET /api/health` (200) không.
- Flow booking gửi email tạo link `/appointments/respond?...` dựa trên biến **`PUBLIC_BASE_URL`** ở backend. Khi chạy thật, biến này phải là domain deploy (ví dụ `https://www.healthbot1.work.gd/api` hoặc domain API thật), **không phải** `http://localhost:8000`.

### 3.1. Chạy dev (khuyến nghị để test UI nhanh)

- Backend: `http://localhost:8000`
- Frontend: `http://localhost:4200`

Thiết lập:
- Backend dùng `.env` theo `.env.example` (có thể để trống `OPENROUTER_API_KEY` để test **fallback**).
- Frontend `environment.ts` trỏ `backendBaseUrl: 'http://localhost:8000'`.

### 3.2. Chạy bằng Docker Compose (mô phỏng deploy)

- Web (Nginx + Angular build): `http://localhost:8080`
- API (internal): expose `8000` trong network compose

Ghi chú:
- Production UI có thể gọi API qua `/api` (tùy cấu hình Nginx proxy).
- Khi test flow email booking, backend dùng `PUBLIC_BASE_URL` để tạo link phản hồi.

## 4) Dữ liệu & tài khoản test

- Dùng `user_id` cố định cho test: `demo` (hoặc `test01`).
- Dữ liệu onboarding mẫu:
  - `age`: 21
  - `gender`: Nam/Nữ/Khác (test đủ 3)
  - `height_cm`: 165
  - `weight_kg`: 58
  - `goal`: “Ngủ tốt hơn”
  - `medical_notes`: để trống + test chuỗi dài

## 5) Quy ước pass/fail & log lỗi

- **Pass**: UI hiển thị đúng luồng, API trả đúng HTTP code + payload hợp lệ, không lỗi console nghiêm trọng.
- **Fail**: crash, dead-end flow, dữ liệu lưu sai user, đặt lịch trùng slot vẫn thành công, safety guardrail không kích hoạt trong tình huống khẩn cấp.

Khi báo lỗi nên kèm:
- Môi trường (dev/docker), URL, thời gian, user_id, bước tái hiện, ảnh chụp màn hình (nếu có), response API (status + body).

## 6) Checklist kiểm thử API (Backend)

### 6.1 Smoke test

- **API-01 — Health check**
  - **Bước**: `GET /health`
  - **Kỳ vọng**: `200` và `{"status":"ok"}`

### 6.2 Onboarding + User

- **API-02 — Tạo mới onboarding**
  - **Bước**: `POST /users/onboarding` với `user_id=demo`
  - **Kỳ vọng**: `200`, trả thông tin user đúng theo payload

- **API-03 — Update onboarding (idempotent theo user_id)**
  - **Bước**: gọi lại `POST /users/onboarding` với cùng `user_id=demo` nhưng đổi `goal`
  - **Kỳ vọng**: `200`, giá trị `goal` được cập nhật

- **API-04 — Lấy hồ sơ user**
  - **Bước**: `GET /users/demo`
  - **Kỳ vọng**: `200`

- **API-05 — Lấy user không tồn tại**
  - **Bước**: `GET /users/not-exist`
  - **Kỳ vọng**: `404`

### 6.3 Family members

- **API-06 — List family members (user tồn tại)**
  - **Bước**: `GET /users/demo/family-members`
  - **Kỳ vọng**: `200` (mảng, có thể rỗng)

- **API-07 — Create family member**
  - **Bước**: `POST /users/demo/family-members` với payload hợp lệ
  - **Kỳ vọng**: `200`, trả `member_user_id` dạng `demo__m{n}`, và có thể dùng `member_user_id` để check-in/chat/summary

- **API-08 — Delete family member**
  - **Bước**: `DELETE /family-members/{member_id}`
  - **Kỳ vọng**: `200`, trả `{"detail":"ok" ...}` và checkins thuộc member bị xóa

### 6.4 Daily check-in

- **API-09 — Create check-in (đã onboarding)**
  - **Bước**: `POST /checkins` với `user_id=demo`
  - **Kỳ vọng**: `200`, `created_at` có giá trị, dữ liệu lưu đúng

- **API-10 — Create check-in (chưa onboarding)**
  - **Bước**: `POST /checkins` với `user_id=not-onboarded`
  - **Kỳ vọng**: `404`, message “Hãy onboarding trước.”

### 6.5 Chat (AI + guardrails + fallback)

- **API-11 — Chat cơ bản (không file)**
  - **Bước**: `POST /chat` (multipart form) với `user_id=demo`, `message="Mình hay căng thẳng và ngủ kém..."`
  - **Kỳ vọng**: `200`, trả `reply` tiếng Việt + có dòng disclaimer cuối

- **API-12 — Chat khi thiếu onboarding**
  - **Bước**: `POST /chat` với `user_id=not-onboarded`
  - **Kỳ vọng**: `200`, `reason="missing_user_profile"`, có CTA “Tạo hồ sơ” trỏ `/onboarding`

- **API-13 — Safety keyword / emergency**
  - **Bước**: `POST /chat` message có dấu hiệu nguy hiểm (ví dụ: “đau ngực và khó thở”)
  - **Kỳ vọng**: `blocked=true`, `intent` emergency, nội dung hướng dẫn xử lý khẩn cấp; không gọi AI

- **API-14 — Chat hỏi “triệu chứng đã check-in chưa”**
  - **Tiền điều kiện**: có check-in gần nhất với `symptoms`
  - **Bước**: hỏi “triệu chứng mình đã điền hôm nay có chưa?”
  - **Kỳ vọng**: trả lời echo đúng triệu chứng, không phụ thuộc LLM

- **API-15 — Chat kèm `conversation_json`**
  - **Bước**: gửi `conversation_json` là mảng role user/assistant hợp lệ; và test trường hợp JSON bậy (string/obj)
  - **Kỳ vọng**: lịch sử hợp lệ được dùng; JSON lỗi bị bỏ qua (không 500)

- **API-16 — Chat kèm file**
  - **Bước**: gửi 1 file `.pdf` hoặc `.docx` hoặc ảnh
  - **Kỳ vọng**: backend parse được text/attachment; nếu model không xử lý ảnh hoặc trả rỗng thì backend trả fallback hướng dẫn (không 500)

- **API-17 — LLM quota/timeout**
  - **Thiết lập**: dùng `OPENROUTER_MODEL` free hoặc set timeout thấp
  - **Bước**: chat bình thường
  - **Kỳ vọng**: backend trả `reason="llm_error"` với message rõ ràng, không crash; với intent booking/reminder có extra hint/CTA phù hợp

### 6.6 Weekly summary

- **API-18 — Weekly summary (có check-in)**
  - **Bước**: `GET /users/demo/weekly-summary`
  - **Kỳ vọng**: `200`, các giá trị avg hợp lý; `stats_text` đúng format

- **API-19 — Weekly summary (chưa có check-in)**
  - **Bước**: user mới onboarding chưa tạo check-in
  - **Kỳ vọng**: `200`, avg = 0, `checkin_days=0`

### 6.7 Reminders

- **API-20 — CRUD reminders**
  - **Bước**: tạo `POST /users/demo/reminders` → list → update `PUT /reminders/{id}` → delete
  - **Kỳ vọng**: dữ liệu nhất quán, update chỉ thay đổi field gửi lên, delete trả ok

### 6.8 Notifications

- **API-21 — Create + list notifications**
  - **Bước**: `POST /users/demo/notifications` rồi `GET /users/demo/notifications`
  - **Kỳ vọng**: list có item mới, sắp theo `created_at` giảm dần

- **API-22 — Mark all read**
  - **Bước**: tạo vài notification unread → `POST /users/demo/notifications/mark-all-read`
  - **Kỳ vọng**: `updated` đúng số lượng, list trả `read=true`

### 6.9 Doctors & booking

- **API-23 — List doctors (seed demo)**
  - **Bước**: `GET /doctors`
  - **Kỳ vọng**: trả đúng danh sách demo (có `name`, `specialty`, `avatar_url`)

- **API-24 — Doctor slots**
  - **Bước**: `GET /doctors/{id}/slots?date_str=2026-04-25`
  - **Kỳ vọng**: trả mảng slot theo khung giờ fixed; slot đã book (pending/confirmed) bị loại

- **API-25 — Create appointment (happy path)**
  - **Bước**: `POST /appointments` với `user_id=demo`, `doctor_id`, `date_str`, `time_str`, `patient_*`
  - **Kỳ vọng**: `200`, status `pending`, email được gửi (nếu cấu hình SMTP) hoặc không làm hỏng flow nếu SMTP trống (tuỳ cấu hình service)

- **API-26 — Prevent double booking**
  - **Bước**: đặt lại cùng doctor/date/time khi đã có pending/confirmed
  - **Kỳ vọng**: `409` với message “Khung giờ này đã được đặt...”

- **API-27 — Appointment respond page**
  - **Bước**: mở link `/appointments/respond?token=...` (không action)
  - **Kỳ vọng**: trang HTML hiển thị thông tin + 2 nút Confirm/Decline

- **API-28 — Confirm/Decline**
  - **Bước**: mở link với `action=confirm` → kiểm tra status appt → notifications + auto reminder one-shot
  - **Kỳ vọng**: status đổi `confirmed`/`declined`; notification được tạo; nếu confirm thì reminder one-shot được tạo

## 7) Checklist kiểm thử UI (Frontend)

> Checklist này tập trung vào trải nghiệm demo theo Figma và các màn được ghi chú trong `README`.

### 7.1 Smoke UI & routing

- **UI-01 — Splash → Onboarding**
  - **Kỳ vọng**: điều hướng đúng, không trắng trang, không lỗi JS nghiêm trọng

- **UI-02 — Onboarding validate**
  - **Bước**: để trống field bắt buộc / nhập giá trị không hợp lệ (âm, chữ)
  - **Kỳ vọng**: có thông báo hợp lý, không gọi API khi form invalid

- **UI-03 — Dashboard sau onboarding**
  - **Kỳ vọng**: hiển thị thông tin cơ bản, điều hướng tới Check-in/Chat/Summary hoạt động

### 7.2 Daily check-in

- **UI-04 — Lưu check-in**
  - **Bước**: nhập ngủ/nước/bước/tâm trạng/triệu chứng → lưu
  - **Kỳ vọng**: có feedback thành công; dữ liệu phản ánh ở weekly summary

- **UI-05 — Edge cases**
  - **Bước**: nhập steps rất lớn, sleep 0, water 0
  - **Kỳ vọng**: không crash, hiển thị hợp lý

### 7.3 Chat

- **UI-06 — Chat khi chưa onboarding**
  - **Bước**: dùng user chưa tạo hồ sơ
  - **Kỳ vọng**: UI hiển thị bot nhắc “Tạo hồ sơ” + CTA chuyển tới onboarding

- **UI-07 — Chat safety**
  - **Bước**: gửi “đau ngực khó thở”
  - **Kỳ vọng**: hiển thị cảnh báo khẩn cấp; không hiển thị “chẩn đoán/kê đơn”

- **UI-08 — CTA theo intent**
  - **Bước**: hỏi “muốn đặt lịch” → CTA `/doctors`; hỏi “nhắc uống thuốc” → CTA `/reminders/new`
  - **Kỳ vọng**: nút CTA xuất hiện đúng nhãn/điều hướng đúng

- **UI-09 — Attachment**
  - **Bước**: gửi file/ảnh (nếu UI hỗ trợ)
  - **Kỳ vọng**: upload thành công; khi AI lỗi/quota thì UI hiển thị fallback message thân thiện

### 7.4 Weekly summary

- **UI-10 — Weekly summary hiển thị**
  - **Kỳ vọng**: có số liệu trung bình + đoạn `stats_text`; xử lý tốt khi chưa có check-in

### 7.5 Doctors & booking

- **UI-11 — Doctors list**
  - **Kỳ vọng**: load danh sách, avatar hiển thị, lọc/tương tác (nếu có)

- **UI-12 — Booking flow**
  - **Bước**: chọn bác sĩ → chọn ngày → xem slot → đặt lịch
  - **Kỳ vọng**: đặt lịch thành công, lịch xuất hiện trong danh sách của user

- **UI-13 — Double booking**
  - **Bước**: cố đặt lại slot đã pending/confirmed
  - **Kỳ vọng**: UI hiển thị lỗi từ backend (409) rõ ràng

### 7.6 Notifications & reminders

- **UI-14 — Notifications**
  - **Bước**: có notification mới (tạo từ booking confirm/decline hoặc test API)
  - **Kỳ vọng**: list hiển thị mới nhất trước; “mark all read” hoạt động

- **UI-15 — Reminders**
  - **Bước**: tạo reminder → sửa → xoá
  - **Kỳ vọng**: trạng thái và nội dung cập nhật đúng, không lệch user

## 8) Kiểm thử phi chức năng (nhẹ)

- **NF-01 — CORS**
  - Dev: frontend `localhost:4200` gọi backend `localhost:8000` không bị CORS block.

- **NF-02 — Lỗi AI không làm hỏng demo**
  - Khi thiếu `OPENROUTER_API_KEY`/gặp `429`/timeout: UI vẫn chạy, backend trả fallback hợp lý.

- **NF-03 — Bảo mật cơ bản**
  - Token link `/appointments/respond`:
    - token sai/hết hạn → trả trang lỗi phù hợp (không lộ stacktrace)
  - Không log lộ API key trong response.

## 9) Tiêu chí nghiệm thu (Definition of Done cho demo MVP)

- Hoàn thành tối thiểu các case **Smoke + Happy path**: API-01..04, API-09, API-11..13, API-18, UI-01, UI-03..04, UI-06..08, UI-10, UI-11..12.
- Không có lỗi blocker: crash, không điều hướng, không lưu được check-in, chat không trả, booking bị trùng slot vẫn đặt được, safety keyword không chặn.

