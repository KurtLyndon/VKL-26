# HLT-vkl-26

Khoi tao project quan ly kiem thu he thong mang noi bo theo yeu cau trong `Requirement.txt`, `Features Description.txt` va `ERD.txt`.

## Cau truc

- `backend`: FastAPI + SQLAlchemy, doc schema theo ERD, ket noi MySQL.
- `frontend`: Vue 3 + Vite, giao dien quan tri cac phan he chinh.

## Backend

1. Tao file `.env` tu [backend/.env.example](D:/Projects/VKL-26/HLT/HLT-vkl-26/backend/.env.example)
2. Cai thu vien:

```powershell
cd D:\Projects\VKL-26\HLT\HLT-vkl-26\backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

3. Chay migration versioned:

```powershell
cd D:\Projects\VKL-26\HLT\HLT-vkl-26\backend
python scripts\migrate.py upgrade
```

4. Chay API:

```powershell
uvicorn app.main:app --reload
```

API mac dinh: `http://localhost:8000`

Neu muon bat scheduler loop nen:

```powershell
$env:SCHEDULER_ENABLED="true"
$env:SCHEDULER_POLL_SECONDS="60"
$env:WORKER_ENABLED="true"
$env:WORKER_POLL_SECONDS="20"
$env:AGENT_DISPATCH_MODE="auto"
$env:AGENT_REQUEST_TIMEOUT_SECONDS="20"
uvicorn app.main:app --reload
```

Neu muon app local tu apply migration pending luc startup:

```powershell
$env:AUTO_APPLY_MIGRATIONS="true"
uvicorn app.main:app --reload
```

## Frontend

1. Tao file `.env` tu [frontend/.env.example](D:/Projects/VKL-26/HLT/HLT-vkl-26/frontend/.env.example)
2. Cai thu vien:

```powershell
cd D:\Projects\VKL-26\HLT\HLT-vkl-26\frontend
npm install
```

3. Chay giao dien:

```powershell
npm run dev
```

Giao dien mac dinh: `http://localhost:5173`

## Pham vi da khoi tao

- CRUD API cho: `agent`, `task`, `operation`, `operation_task`, `target`, `target_attribute_definition`, `target_attribute_value`, `target_group`, `vulnerability`, `vulnerability_script`, `scan_result`, `scan_result_finding`, `report_template`.
- CRUD API mo rong cho: `operation_execution`, `task_execution`, `generated_report`, `report_snapshot`.
- Runtime API cho launch operation, cap nhat task execution status va tong hop runtime overview.
- Runtime API bo sung heartbeat cho agent/task execution va endpoint discovery contract `GET /api/v1/agents/runtime/execute-contract`.
- Scheduler runner cho `cron` va `interval`, co API chay tay va background loop qua env.
- Worker runner xu ly `task_execution` theo thu tu, mock-run agent, parse ket qua va luu `scan_result`.
- Import/export ket qua operation qua `JSON`, `CSV`, `XLSX`, va import lai du lieu scan bang `JSON`.
- Frontend co man `Operation Designer`, `Execution Monitor`, `Finding Explorer` de thao tac workflow va loc ket qua de demo.
- Worker co the dispatch HTTP toi agent that theo contract `execute`, ho tro ca che do sync va async heartbeat/status callback, hoac fallback ve mock runner.
- Dashboard tong quan cho frontend.
- Kien truc tach rieng de sau nay docker hoa, them worker, scheduler, parser agent va export report.
- Co migration SQL versioned trong `backend/migrations/versions`.
- Co runner migration local trong `backend/scripts/migrate.py`.
- Co snapshot SQL cu trong `backend/database` de tham khao va bootstrap thu cong.
- Co nhat ky tien do trong `docs/WORKLOG.md` de lan sau tiep tuc.
- Code parser tung agent duoc tach rieng trong `backend/app/services/agents`.
- Parser hien co cho `nmap` (XML + fallback text), `nuclei` (JSONL + fallback text), `acunetix` (JSON + fallback text).
- Tai lieu contract agent that: [docs/AGENT_RUNTIME_CONTRACT.md](D:/Projects/VKL-26/HLT/HLT-vkl-26/docs/AGENT_RUNTIME_CONTRACT.md)

## Migration versioned

Quy uoc hien tai:

- File migration nam trong `backend/migrations/versions`.
- Ten file theo mau `<version>__<ten>.sql`.
- Runner luu version da apply trong bang `schema_migrations`.
- Runner tu tao database neu chua ton tai.
- Runner tu stamp baseline `001/002` neu phat hien local DB da duoc tao tu SQL cu hoac `create_all`, tranh apply lai seed mau.

Lenh hay dung:

```powershell
cd D:\Projects\VKL-26\HLT\HLT-vkl-26\backend
python scripts\migrate.py status
python scripts\migrate.py upgrade
```

Tai lieu chi tiet: [docs/MIGRATIONS.md](D:/Projects/VKL-26/HLT/HLT-vkl-26/docs/MIGRATIONS.md)

## Khoi tao database nhanh

Luong uu tien la migration runner. Neu can bootstrap thu cong hoac doi chieu schema, van co the chay snapshot SQL:

```powershell
mysql -u root -p < backend\database\001_init_schema.sql
mysql -u root -p < backend\database\002_seed_sample_data.sql
```

Script Python seed hien goi migration runner truoc, sau do chi chen du lieu neu database chua co sample data:

```powershell
cd D:\Projects\VKL-26\HLT\HLT-vkl-26\backend
python scripts\seed_data.py
```

## De xuat buoc tiep theo

1. Them migration `003+` cho cac thay doi schema tiep theo.
2. Dung 1 agent service that mau theo `docs/AGENT_RUNTIME_CONTRACT.md`.
3. Them export PDF va bo loc dashboard.
4. Mo rong auth cho runtime callback neu dua agent that vao moi truong that.
5. Can nhac Alembic sau nay neu can autogenerate/revision phuc tap hon.
