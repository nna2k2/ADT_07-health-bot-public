# Chạy Health Bot trên server

## Cách 1 — Docker Compose (khuyến nghị)

1. Tạo `backend/.env` (copy từ `backend/.env.example`), bắt buộc có `OPENROUTER_API_KEY`.
2. Trong `backend/.env`, thêm hoặc chỉnh **`CORS_ORIGINS`** cho đúng URL người dùng mở app, ví dụ:
   - Chạy compose mặc định: `http://localhost:8080,http://127.0.0.1:8080`
   - Server có domain: `https://ten-mien-cua-ban.com`
3. Từ thư mục `health-bot/`:

```bash
docker compose up --build -d
```

4. Trình duyệt: **`http://<IP-máy-chủ>:8080`**

- Frontend build production dùng `environment.prod.ts`: API gọi tới **`/api`** (cùng origin).
- Nginx trong container `web` proxy `/api/` → service `api` (uvicorn cổng 8000).

Đổi cổng public (ví dụ 80): sửa `docker-compose.yml` mục `web.ports` thành `"80:80"`.

---

## Cách 2 — Không Docker (VPS Linux)

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# Tạo .env, set CORS_ORIGINS=https://domain-cua-ban
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm ci
# Nếu API full URL khác domain: sửa src/environments/environment.prod.ts → backendBaseUrl
npm run build -- --configuration=production
```

Copy nội dung `frontend/dist/health-bot-frontend/browser/` lên thư mục web (Nginx `root`).

### Nginx (ví dụ SPA + `/api` cùng host)

```nginx
location /api/ {
    proxy_pass http://127.0.0.1:8000/;
    proxy_read_timeout 120s;
    client_max_body_size 25m;
}
location / {
    try_files $uri $uri/ /index.html;
}
```

---

## Ghi chú

- **HTTPS**: dùng Let’s Encrypt (certbot) hoặc reverse proxy (Cloudflare) trước Nginx.
- **SQLite**: file DB nằm trong thư mục chạy backend; backup file `.db` định kỳ.
- **Web Speech (mic → chữ)**: thường cần **HTTPS** hoặc `localhost` mới ổn định trên một số trình duyệt.
