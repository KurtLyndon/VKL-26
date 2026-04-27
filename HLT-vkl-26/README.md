# HLT-vkl-26

Project quản lý kiểm thử hệ thống mạng nội bộ 

## Cấu trúc

- `backend`: FastAPI + SQLAlchemy, bám schema theo ERD, kết nối MySQL.
- `frontend`: Vue 3 + Vite, giao diện quản trị các phân hệ chính.
- `agents/nmap-agent-demo`: agent Nmap demo chạy riêng, để mang sang Kali/VM khác.

## Backend

Runtime khuyến nghị cho backend: `Python 3.12`.

Lý do:

- ổn định hơn cho `FastAPI + SQLAlchemy + PyMySQL`
- hợp với hướng Docker hóa sau này, vì dễ đồng bộ với image như `python:3.12-slim`
- tránh các vấn đề tương thích sớm với `Python 3.14`

1. Tạo file `.env` từ [backend/.env.example](D:/Projects/VKL-26/HLT/HLT-vkl-26/backend/.env.example)
2. Cài thư viện:

```powershell
cd D:\Projects\VKL-26\HLT\HLT-vkl-26\backend
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

3. Chạy migration versioned:

```powershell
cd D:\Projects\VKL-26\HLT\HLT-vkl-26\backend
python -m scripts.migrate upgrade
python -m scripts.seed_data
```

4. Chạy API:

```powershell
uvicorn app.main:app --reload
```

API mặc định: `http://localhost:8000`

Nếu muốn bật scheduler loop nền:

```powershell
$env:SCHEDULER_ENABLED="true"
$env:SCHEDULER_POLL_SECONDS="60"
$env:WORKER_ENABLED="true"
$env:WORKER_POLL_SECONDS="20"
$env:AGENT_DISPATCH_MODE="auto"
$env:AGENT_REQUEST_TIMEOUT_SECONDS="20"
uvicorn app.main:app --reload
```

Nếu muốn app local tự apply migration pending lúc startup:

```powershell
$env:AUTO_APPLY_MIGRATIONS="true"
uvicorn app.main:app --reload
```

## Frontend

1. Tạo file `.env` từ [frontend/.env.example](D:/Projects/VKL-26/HLT/HLT-vkl-26/frontend/.env.example)
2. Cài thư viện:

```powershell
cd D:\Projects\VKL-26\HLT\HLT-vkl-26\frontend
npm install
```

3. Chạy giao diện:

```powershell
npm run dev
```

Giao diện mặc định: `http://localhost:5173`

Đăng nhập mặc định cho bản dev/mock:

- username: `admin`
- password: `Admin@123`

## Agent Demo Riêng

Đã có một agent Nmap demo tách riêng tại [agents/nmap-agent-demo/README.md](D:/Projects/VKL-26/HLT/HLT-vkl-26/agents/nmap-agent-demo/README.md) để triển khai trên Kali hoặc VM khác.

Mục tiêu của project con này:

- nhận `POST /execute` từ backend
- trả `accepted` ngay
- callback heartbeat và completion về backend
- tự gọi normalize kết quả `nmap` sau khi quét xong
- hỗ trợ `mock` mode để test nhanh và `real` mode để gọi binary `nmap`

## Phạm vi đã khởi tạo

- CRUD API cho: `agent`, `task`, `operation`, `operation_task`, `target`, `target_attribute_definition`, `target_attribute_value`, `target_group`, `vulnerability`, `vulnerability_script`, `scan_result`, `scan_result_finding`, `report_template`.
- CRUD API mở rộng cho: `operation_execution`, `task_execution`, `generated_report`, `report_snapshot`.
- Runtime API cho launch operation, cập nhật task execution status và tổng hợp runtime overview.
- Runtime API bổ sung heartbeat cho agent/task execution và endpoint discovery contract `GET /api/v1/agents/runtime/execute-contract`.
- Auth cơ bản theo nhóm tài khoản (RBAC): login, nhóm tài khoản, tài khoản và bật/tắt quyền theo nhóm.
- Scheduler runner cho `cron` và `interval`, có API chạy tay và background loop qua env.
- Worker runner xử lý `task_execution` theo thứ tự, mock-run agent, parse kết quả và lưu `scan_result`.
- Có endpoint `POST /api/v1/demo/mock-flow` để chạy nhanh end-to-end mock flow.
- Có thể import dữ liệu CVE từ Excel STMNC, bao gồm cả `POC` dạng text hoặc file script.
- Import/export kết quả operation qua `JSON`, `CSV`, `XLSX`, và import lại dữ liệu scan bằng `JSON`.
- Frontend có màn `Operation Designer`, `Execution Monitor`, `Finding Explorer` để thao tác workflow và lọc kết quả demo.
- Worker có thể dispatch HTTP tới agent thật theo contract `execute`, hỗ trợ cả chế độ sync và async heartbeat/status callback, hoặc fallback về mock runner.
- Dashboard tổng quan cho frontend.
- Kiến trúc tách riêng để sau này Docker hóa, thêm worker, scheduler, parser agent và export report.
- Có migration SQL versioned trong `backend/migrations/versions`.
- Có runner migration local trong `backend/scripts/migrate.py`.
- Có snapshot SQL cũ trong `backend/database` để tham khảo và bootstrap thủ công.
- Có nhật ký tiến độ trong `docs/WORKLOG.md` để lần sau tiếp tục.
- Code parser từng agent được tách riêng trong `backend/app/services/agents`.
- Parser hiện có cho `nmap` (XML + fallback text), `nuclei` (JSONL + fallback text), `acunetix` (JSON + fallback text).
- Có kho lưu trữ script POC tại `backend/data/poc_repository` để giữ bản sao script xác minh.
- Tài liệu contract agent thật: [docs/AGENT_RUNTIME_CONTRACT.md](D:/Projects/VKL-26/HLT/HLT-vkl-26/docs/AGENT_RUNTIME_CONTRACT.md)

## Migration Versioned

Quy ước hiện tại:

- File migration nằm trong `backend/migrations/versions`.
- Tên file theo mẫu `<version>__<ten>.sql`.
- Runner lưu version đã apply trong bảng `schema_migrations`.
- Runner tự tạo database nếu chưa tồn tại.
- Runner tự stamp baseline `001/002` nếu phát hiện local DB đã được tạo từ SQL cũ hoặc `create_all`, tránh apply lại seed mẫu.

Lệnh hay dùng:

```powershell
cd D:\Projects\VKL-26\HLT\HLT-vkl-26\backend
python -m scripts.migrate status
python -m scripts.migrate upgrade
```

Tài liệu chi tiết: [docs/MIGRATIONS.md](D:/Projects/VKL-26/HLT/HLT-vkl-26/docs/MIGRATIONS.md)

## Khởi tạo Database Nhanh

Luồng ưu tiên là migration runner. Nếu cần bootstrap thủ công hoặc đối chiếu schema, vẫn có thể chạy snapshot SQL:

```powershell
mysql -u root -p < backend\database\001_init_schema.sql
mysql -u root -p < backend\database\002_seed_sample_data.sql
```

Script Python seed hiện gọi migration runner trước, sau đó chỉ chèn dữ liệu nếu database chưa có sample data:

```powershell
cd D:\Projects\VKL-26\HLT\HLT-vkl-26\backend
python -m scripts.seed_data
```

Import CVE từ Excel:

```powershell
cd D:\Projects\VKL-26\HLT\HLT-vkl-26\backend
python -m scripts.import_vulnerabilities_from_xlsx "D:\Projects\VKL-26\STMNC\1-Codes-v1.8-19-03-2026.xlsx"
```

## Đề xuất bước tiếp theo

1. Test end-to-end mock flow và rà soát nhẹ UI/encoding trong browser.
2. Deploy và test `agents/nmap-agent-demo` trên máy Kali/VM khi máy đủ tài nguyên.
3. Thêm export PDF và bộ lọc dashboard nâng cao hơn.
4. Mở rộng auth cho runtime callback nếu đưa agent thật vào môi trường thật.
5. Thêm migration `004+` khi schema đổi tiếp.
