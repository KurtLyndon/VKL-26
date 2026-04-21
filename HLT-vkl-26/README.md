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

3. Chay API:

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
- Scheduler runner cho `cron` va `interval`, co API chay tay va background loop qua env.
- Worker runner xu ly `task_execution` theo thu tu, mock-run agent, parse ket qua va luu `scan_result`.
- Import/export ket qua operation qua `JSON`, `CSV`, `XLSX`, va import lai du lieu scan bang `JSON`.
- Frontend co man `Operation Designer`, `Execution Monitor`, `Finding Explorer` de thao tac workflow va loc ket qua de demo.
- Dashboard tong quan cho frontend.
- Kien truc tach rieng de sau nay docker hoa, them worker, scheduler, parser agent va export report.
- Co SQL khoi tao schema va seed mau trong `backend/database`.
- Co nhat ky tien do trong `docs/WORKLOG.md` de lan sau tiep tuc.
- Code parser tung agent duoc tach rieng trong `backend/app/services/agents`.
- Parser hien co cho `nmap` (XML + fallback text), `nuclei` (JSONL + fallback text), `acunetix` (JSON + fallback text).

## Khoi tao database nhanh

Neu muon tao schema bang SQL thay vi de app tu `create_all`, chay lan luot:

```powershell
mysql -u root -p < backend\database\001_init_schema.sql
mysql -u root -p < backend\database\002_seed_sample_data.sql
```

Hoac dung script Python seed sau khi da cai dependency:

```powershell
cd D:\Projects\VKL-26\HLT\HLT-vkl-26\backend
python scripts\seed_data.py
```

## De xuat buoc tiep theo

1. Them Alembic migration thay cho `create_all`.
2. Bo sung auth va phan quyen.
3. Them export PDF va bo loc dashboard.
4. Them worker/dispatch that toi agent thuc te.
5. Hoan thien migration va auth.
