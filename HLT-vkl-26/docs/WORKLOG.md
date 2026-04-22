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
- Them migration versioned local trong `backend/migrations/versions` va CLI `python scripts\migrate.py`.
- Thay `Base.metadata.create_all(...)` bang migration check/apply co dieu khien boi `AUTO_APPLY_MIGRATIONS`.
- Bo sung baseline stamping cho database cu da tao bang SQL snapshot hoac `create_all`, tranh xung dot seed mau.
- Bo sung giao thuc runtime cho agent that: discovery contract, agent heartbeat, task heartbeat, va callback hoan tat task.
- Worker/dispatch da ho tro ca 2 luong sync va async:
  - sync: agent tra `raw_output` ngay trong `/execute`
  - async: agent tra `accepted/running`, sau do gui heartbeat va callback status ve backend
- Them tai lieu `docs/AGENT_RUNTIME_CONTRACT.md` de dev agent rieng va debug de hon.
- Them project agent mau tach rieng tai `agents/nmap-agent-demo` de co the copy sang may Kali/VM khac.
- Agent mau ho tro `mock` mode va `real` mode, callback heartbeat/status/normalize nguoc ve backend.
- Them mau `systemd` service va huong dan deploy rieng cho agent Nmap demo.
- Bo sung auth RBAC co ban theo nhom tai khoan: login, token, nhom tai khoan, tai khoan va phan quyen theo nhom.
- Frontend da co man dang nhap, man quan ly quyen theo nhom, va menu cap 1/cap 2 loc theo permission.
- Bo sung `mock demo flow` de launch operation + worker tu dong trong 1 buoc cho demo noi bo.
- Tinh gon sidebar thanh menu accordion: chi mo 1 menu cap 1 tai mot thoi diem, menu cap 2 tu dong thu gon/expand tuong ung.
- Khi chuyen menu va doi view, panel ben phai tu focus/scroll len dau de thao tac nhanh hon.

### Trang thai tam thoi

- Co the dev tiep tu local, khong phu thuoc ngay vao internet.
- Chua push GitHub vi moi truong hien tai khong goi duoc `git`.
- Chua chay `npm install` / `pip install`, nen frontend/backend chua duoc boot runtime thuc te trong workspace nay.

### Buoc tiep theo de lam tiep

1. Them migration `003+` cho thay doi schema tiep theo.
2. Thu nghiem `agents/nmap-agent-demo` tren may Kali/VM va noi voi backend that.
3. Them export PDF.
4. Ra soat lai UI/encoding trong browser va build frontend.
5. Can nhac Alembic neu sau nay can autogenerate/revision phuc tap hon.
