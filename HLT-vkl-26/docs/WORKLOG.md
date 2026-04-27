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
- Bổ sung luồng import CVE từ file Excel STMNC, hỗ trợ map `Mã`, `Mức độ`, `Nguy cơ mất ATTT`, `Kiến nghị, đề xuất`, `Kiểm chứng`.
- Mở rộng `vulnerability` để lưu được cả `poc_text` và `poc_file_name`.
- Thêm kho lưu trữ POC script tại `backend/data/poc_repository` để giữ bản sao script xác minh phục vụ đẩy xuống agent thực thi.
- Script import sẽ tự copy file POC vào kho lưu trữ này và tạo/cập nhật `vulnerability_script` tương ứng.
- Mở rộng cụm quản lý `Mục tiêu`:
  - thêm UI riêng cho `Target`, `Target Attribute`, `Target Group`
  - hỗ trợ gán thuộc tính động cho từng target, cho phép value `null`
  - hỗ trợ gán target vào nhiều nhóm
  - hỗ trợ import `Excel/CSV`, tự sinh attribute mới theo cột mới
  - nhóm lại menu sidebar để `Mục tiêu` có 3 menu con riêng
- Bổ sung sort cho các bảng danh sách trên UI:
  - mặc định load theo `ID` giảm dần nếu bảng có cột `ID`
  - click tiêu đề cột để đổi qua lại `giảm dần <-> tăng dần`
- Bổ sung chuẩn hóa và phân giải `Dải IP` cho target:
  - hỗ trợ nhiều dải/IP cách nhau bằng dấu phẩy
  - tự chuẩn hóa các pattern lỗi như `[1 - 3]`, `[1_3]` về `[1-3]`
  - thêm hàm phân giải để mở rộng `192.168.[1-3].0/24` thành 3 dải con phục vụ khớp scan result
- Đổi theme UI sang xanh lá cây đậm làm chủ đạo, vùng làm việc kem xương, chữ đen trên nền sáng và chữ trắng trên nền xanh đậm.
- Tinh chỉnh lại trạng thái menu sidebar:
  - hover đổi nền và màu chữ rồi trả về bình thường khi leave
  - active có màu riêng khác hover
  - sidebar dùng nền `#064509`
  - vùng nội dung chính chuyển sang nền trắng kem sáng hơn

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
