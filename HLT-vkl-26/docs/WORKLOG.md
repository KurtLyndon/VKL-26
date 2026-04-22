# Worklog

## 2026-04-21

### Đã hoàn thành

- Tạo skeleton project full-stack `HLT-vkl-26`.
- Dựng backend `FastAPI + SQLAlchemy + MySQL config`.
- Khai báo model/schema theo ERD cho nhóm Agent, Task, Operation, Target, Vulnerability, Scan Result, Report.
- Tạo CRUD API ban đầu và dashboard summary.
- Dựng frontend `Vue 3 + Vite` với dashboard và các màn quản trị resource.
- Thêm `backend/database/001_init_schema.sql` để khởi tạo schema MySQL.
- Thêm `backend/database/002_seed_sample_data.sql` và `backend/scripts/seed_data.py` để tạo dữ liệu mẫu.
- Thêm execution flow cơ bản: `operation_execution`, `task_execution`, launch operation.
- Tách parser service theo từng agent trong `backend/app/services/agents/nmap` và `backend/app/services/agents/nuclei`.
- Thêm API normalize scan result thành `scan_result` + `scan_result_finding`.
- Thêm runtime control: launch operation từ UI, cập nhật task execution status và runtime overview.
- Thêm scheduler runner cho operation với `cron`/`interval`, có API run-now và background loop qua env.
- Nâng parser `nmap` đọc XML, `nuclei` đọc JSONL, và thêm khung parser riêng cho `acunetix`.
- Thêm worker runner mock cho `nmap`, `nuclei`, `acunetix`; xử lý task theo thứ tự và tự sinh scan result/finding.
- Thêm import/export kết quả operation qua `JSON`, `CSV`, `XLSX`, và UI quản lý lịch sử import/export.
- Thêm UI `Operation Designer`, `Execution Monitor`, `Finding Explorer` để sắp task và lọc execution/finding.
- Worker hỗ trợ dispatch HTTP tới agent thật theo `host/ip_address + port`, và fallback mock runner khi chưa có agent service.
- Thêm migration versioned local trong `backend/migrations/versions` và CLI `python scripts\migrate.py`.
- Thay `Base.metadata.create_all(...)` bằng migration check/apply có điều khiển bởi `AUTO_APPLY_MIGRATIONS`.
- Bổ sung baseline stamping cho database cũ đã tạo bằng SQL snapshot hoặc `create_all`, tránh xung đột seed mẫu.
- Bổ sung giao thức runtime cho agent thật: discovery contract, agent heartbeat, task heartbeat, và callback hoàn tất task.
- Worker/dispatch đã hỗ trợ cả 2 luồng sync và async:
  - sync: agent trả `raw_output` ngay trong `/execute`
  - async: agent trả `accepted/running`, sau đó gửi heartbeat và callback status về backend
- Thêm tài liệu `docs/AGENT_RUNTIME_CONTRACT.md` để dev agent riêng và debug dễ hơn.
- Thêm project agent mẫu tách riêng tại `agents/nmap-agent-demo` để có thể copy sang máy Kali/VM khác.
- Agent mẫu hỗ trợ `mock` mode và `real` mode, callback heartbeat/status/normalize ngược về backend.
- Thêm mẫu `systemd` service và hướng dẫn deploy riêng cho agent Nmap demo.
- Bổ sung auth RBAC cơ bản theo nhóm tài khoản: login, token, nhóm tài khoản, tài khoản và phân quyền theo nhóm.
- Frontend đã có màn đăng nhập, màn quản lý quyền theo nhóm, và menu cấp 1/cấp 2 lọc theo permission.
- Bổ sung `mock demo flow` để launch operation + worker tự động trong 1 bước cho demo nội bộ.
- Tinh gọn sidebar thành menu accordion: chỉ mở 1 menu cấp 1 tại một thời điểm, menu cấp 2 tự động thu gọn/expand tương ứng.
- Khi chuyển menu và đổi view, panel bên phải tự focus/scroll lên đầu để thao tác nhanh hơn.

### Trạng thái tạm thời

- Có thể dev tiếp từ local, không phụ thuộc ngay vào internet.
- Chưa push GitHub vì môi trường hiện tại không gọi được `git` trong terminal tool, nhưng user vẫn có thể commit/push thủ công.
- Chưa chạy `npm install` / `pip install` trong mọi lượt xác minh, nên frontend/backend chưa phải lúc nào cũng được boot runtime thực tế trong workspace này.

### Bước tiếp theo để làm tiếp

1. Thử nghiệm `mock demo flow` trực tiếp trong browser và rà lại các lỗi UI/encoding còn sót.
2. Thử `agents/nmap-agent-demo` trên máy Kali/VM và nối với backend thật khi máy đủ tài nguyên.
3. Thêm export PDF.
4. Rà soát lại UI/encoding trong browser và build frontend.
5. Cân nhắc Alembic nếu sau này cần autogenerate/revision phức tạp hơn.
