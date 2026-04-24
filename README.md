## Health Care Bot MVP (Wellness)

MVP bot chăm sóc sức khỏe tổng quát (wellness), bám UI theo Figma và dễ demo đồ án.

**Lưu ý an toàn**: Bot này **không chẩn đoán bệnh**, **không kê đơn thuốc**, **không thay thế bác sĩ**. Nếu có dấu hiệu nguy hiểm, hãy đến cơ sở y tế gần nhất hoặc gọi cấp cứu.

### 1) Cấu trúc thư mục

- `frontend/`: Angular (standalone components, router, reactive forms)
- `backend/`: FastAPI + SQLite + OpenRouter

---

## Backend (FastAPI)

### Yêu cầu

- Python 3.11+

### Cài đặt

```bash
cd backend
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
```

### Cấu hình OpenRouter

Copy `.env.example` thành `.env` và điền key:

```bash
cd backend
copy .env.example .env
```

Các biến môi trường:

- `OPENROUTER_API_KEY`: API key (bắt buộc nếu muốn gọi AI)
- `OPENROUTER_MODEL`: mặc định `openrouter/free` (có thể đổi sang model có hậu tố `:free`)
- `OPENROUTER_MULTIMODAL_MODEL`: (khuyến nghị khi gửi **ảnh**/media) model vision/multimodal trên OpenRouter. Nếu để trống, request ảnh vẫn dùng `OPENROUTER_MODEL` — model chỉ-text có thể lỗi hoặc vẫn dùng cùng model free và dễ gặp **429 rate limit** từ phía nhà cung cấp (ví dụ Google AI Studio với Gemma free).
- `OPENROUTER_BASE_URL`: mặc định `https://openrouter.ai/api/v1`
- `OPENROUTER_TIMEOUT_S`: timeout HTTP (giây); khi gửi ảnh có thể cần tăng (ví dụ `60`)

**Lỗi 429 khi dùng ảnh / model free**

Đây không phải lỗi code: OpenRouter báo upstream (Google, v.v.) **tạm chặn** do hết hạn mức miễn phí. Cách xử lý thực tế:

1. **Thử lại sau vài phút** — backend đã tự retry vài lần khi gặp 429.
2. **Đổi model** trên [OpenRouter Models](https://openrouter.ai/models): chọn model hỗ trợ vision, ưu tiên model khác hoặc có trả phí/ổn định hơn.
3. **`OPENROUTER_MULTIMODAL_MODEL`** — tách model cho chat có ảnh (vision) khác model chat chỉ chữ, để tránh model free vision bị nghẽn.
4. **Nạp credit / tích hợp key riêng** theo [OpenRouter settings](https://openrouter.ai/settings/integrations) để tăng hạn mức (thông báo lỗi của OpenRouter cũng gợi ý hướng này).

Bot **đã hỗ trợ ảnh** ở tầng API (gửi `image_url` base64 qua OpenRouter); vấn đề hiện tại là **hạn mức / model**, không phải thiếu tính năng phía app.
- `TRIAGE_EXAMPLES_PATH`: (tùy chọn) đường dẫn tới file examples `.jsonl/.json` để few-shot (dùng script builder)
- `TRIAGE_EXAMPLES_LIMIT`: (tùy chọn) số examples đưa vào prompt (mặc định 6)

Ví dụ đổi model:

- `OPENROUTER_MODEL=meta-llama/llama-3.1-8b-instruct:free` (ví dụ; tùy thời điểm OpenRouter cung cấp)

### Chạy server

```bash
cd backend
.\.venv\Scripts\uvicorn app.main:app --reload --port 8000
```

### Test nhanh bằng curl

#### 1) Onboarding

```bash
curl -X POST http://localhost:8000/users/onboarding ^
  -H "Content-Type: application/json" ^
  -d "{\"user_id\":\"demo\",\"age\":21,\"gender\":\"Nam\",\"height_cm\":165,\"weight_kg\":58,\"goal\":\"Ngủ tốt hơn\",\"medical_notes\":\"\"}"
```

#### 2) Daily check-in

```bash
curl -X POST http://localhost:8000/checkins ^
  -H "Content-Type: application/json" ^
  -d "{\"user_id\":\"demo\",\"sleep_hours\":6.5,\"water_liters\":1.8,\"steps\":6240,\"mood\":\"ổn\",\"symptoms\":\"\"}"
```

#### 3) Chat

```bash
curl -X POST http://localhost:8000/chat ^
  -H "Content-Type: application/json" ^
  -d "{\"user_id\":\"demo\",\"message\":\"Mình hay căng thẳng và ngủ kém, nên làm gì?\"}"
```

#### 4) Weekly summary

```bash
curl http://localhost:8000/users/demo/weekly-summary
```

#### Safety rule (không gọi AI)

```bash
curl -X POST http://localhost:8000/chat ^
  -H "Content-Type: application/json" ^
  -d "{\"user_id\":\"demo\",\"message\":\"Tôi bị đau ngực và khó thở\"}"
```

---

## Frontend (Angular)

### Yêu cầu

- Node.js 18+ (khuyến nghị)

### Cài đặt & chạy

```bash
cd frontend
npm install
npm start
```

Mặc định Angular chạy `http://localhost:4200` và gọi backend ở `http://localhost:8000`.

### Nối frontend với backend

Sửa `frontend/src/environments/environment.ts`:

- `backendBaseUrl: 'http://localhost:8000'`

### Build production & chạy trên server

- File `frontend/src/environments/environment.prod.ts`: mặc định `backendBaseUrl: '/api'` (cùng domain, Nginx proxy `/api` → FastAPI).
- Build: `cd frontend && npm run build -- --configuration=production`
- **Docker**: từ thư mục `health-bot/`, xem `deploy/README-SERVER.md` và chạy `docker compose up --build -d` (app tại cổng **8080**).

---

## Ghi chú demo

- Flow: `Splash → Onboarding → Dashboard → (Check-in / Chat / Weekly summary / Profile)`
- Chat sẽ trả lời tiếng Việt; nếu chưa cấu hình `OPENROUTER_API_KEY` thì backend sẽ trả message fallback để demo UI vẫn chạy.

---

## Build few-shot examples từ dataset (tùy chọn)

Dataset `ai-medical-chatbot.csv` có cột `Doctor` chứa nhiều chỗ kê đơn/liều dùng. Script dưới đây sẽ **sanitize** theo triage (loại bỏ kê đơn/liều lượng, giảm chắc chắn) và xuất ra examples để làm few-shot.

```bash
cd backend
.\.venv\Scripts\python -m app.tools.triage_dataset_builder ^
  --input "E:\Dowload\TEST\Cuộc thi DGS Xanh\ai-medical-chatbot.csv\ai-medical-chatbot.csv" ^
  --output "E:\THAC SI\UIUX\health-bot\backend\app\data\triage_examples.jsonl" ^
  --limit 200
```

Sau đó set trong `backend/.env`:

```bash
TRIAGE_EXAMPLES_PATH=E:\THAC SI\UIUX\health-bot\backend\app\data\triage_examples.jsonl
TRIAGE_EXAMPLES_LIMIT=6
```

