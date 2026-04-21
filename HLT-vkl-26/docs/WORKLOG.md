# Worklog

## 2026-04-21

### Da hoan thanh

- Tao skeleton project full-stack `HLT-vkl-26`.
- Dung backend `FastAPI + SQLAlchemy + MySQL config`.
- Khai bao model/schema theo ERD cho nhom Agent, Task, Operation, Target, Vulnerability, Scan Result, Report.
- Tao CRUD API ban dau va dashboard summary.
- Dung frontend `Vue 3 + Vite` voi dashboard va cac man quan tri resource.
- Them `backend/database/001_init_schema.sql` de khoi tao schema MySQL.
- Them `backend/database/002_seed_sample_data.sql` va `backend/scripts/seed_data.py` de tao du lieu mau.

### Trang thai tam thoi

- Co the dev tiep tu local, khong phu thuoc ngay vao internet.
- Chua push GitHub vi moi truong hien tai khong goi duoc `git`.
- Chua chay `npm install` / `pip install`, nen frontend/backend chua duoc boot runtime thuc te trong workspace nay.

### Buoc tiep theo de lam tiep

1. Them migration versioned (Alembic hoac thu muc SQL migration co quy uoc version).
2. Them bang va API cho `operation_execution`, `task_execution`, `generated_report`, `report_snapshot`.
3. Lam service parser chuan hoa output cho `nmap` va `nuclei`.
4. Lam scheduler runner cho operation.
5. Them import/export CSV, Excel, JSON.
