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
- Them execution flow co ban: `operation_execution`, `task_execution`, launch operation.
- Tach parser service theo tung agent trong `backend/app/services/agents/nmap` va `backend/app/services/agents/nuclei`.
- Them API normalize scan result thanh `scan_result` + `scan_result_finding`.
- Them runtime control: launch operation tu UI, cap nhat task execution status va runtime overview.
- Them scheduler runner cho operation voi `cron`/`interval`, co API run-now va background loop qua env.
- Nang parser `nmap` doc XML, `nuclei` doc JSONL, va them khung parser rieng cho `acunetix`.
- Them worker runner mock cho `nmap`, `nuclei`, `acunetix`; xu ly task theo thu tu va tu sinh scan result/finding.
- Them import/export ket qua operation qua `JSON`, `CSV`, `XLSX`, va UI quan ly lich su import/export.
- Them UI `Operation Designer`, `Execution Monitor`, `Finding Explorer` de sap task va loc execution/finding.
- Worker ho tro dispatch HTTP toi agent that theo `host/ip_address + port`, va fallback mock runner khi chua co agent service.

### Trang thai tam thoi

- Co the dev tiep tu local, khong phu thuoc ngay vao internet.
- Chua push GitHub vi moi truong hien tai khong goi duoc `git`.
- Chua chay `npm install` / `pip install`, nen frontend/backend chua duoc boot runtime thuc te trong workspace nay.

### Buoc tiep theo de lam tiep

1. Them migration versioned (Alembic hoac thu muc SQL migration co quy uoc version).
2. Hoan thien giao thuc agent that, callback va heartbeat.
3. Them export PDF.
4. Hoan thien migration versioned.
5. Them auth va phan quyen.
