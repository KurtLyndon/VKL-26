# Worklog

## 2026-04-21

### Đã hoàn thành

- Tạo skeleton project full-stack `HLT-vkl-26`.
- Dựng backend `FastAPI + SQLAlchemy + MySQL`.
- Khai báo model và schema theo ERD cho Agent, Task, Operation, Target, Vulnerability, Scan Result, Report.
- Dựng CRUD API ban đầu và dashboard summary.
- Dựng frontend `Vue 3 + Vite` với dashboard và các màn quản trị resource.
- Thêm `backend/database/001_init_schema.sql` để khởi tạo schema MySQL.
- Thêm `backend/database/002_seed_sample_data.sql` và `backend/scripts/seed_data.py` để seed dữ liệu.
- Thêm execution flow cơ bản: `operation_execution`, `task_execution`, launch operation.
- Tách parser service theo từng agent trong `backend/app/services/agents/nmap`, `nuclei`, `acunetix`.
- Thêm API normalize scan result thành `scan_result` và `scan_result_finding`.
- Thêm runtime control: launch operation từ UI, cập nhật task execution status và runtime overview.
- Thêm scheduler runner cho operation với `cron` và `interval`, có API run-now và background loop qua env.
- Nâng parser `nmap` đọc XML, `nuclei` đọc JSONL và bổ sung parser riêng cho `acunetix`.
- Thêm worker runner mock cho `nmap`, `nuclei`, `acunetix`; xử lý task theo thứ tự và tự sinh scan result/finding.
- Thêm import/export kết quả operation qua `JSON`, `CSV`, `XLSX`, cùng UI quản lý lịch sử import/export.
- Thêm UI `Operation Designer`, `Execution Monitor`, `Finding Explorer`.
- Worker hỗ trợ dispatch HTTP tới agent thật theo `host/ip_address + port` và fallback mock runner.
- Thêm migration versioned local trong `backend/migrations/versions` và CLI `python scripts\\migrate.py`.
- Thay `Base.metadata.create_all(...)` bằng migration check/apply điều khiển bởi `AUTO_APPLY_MIGRATIONS`.
- Bổ sung baseline stamping cho database cũ để tránh xung đột seed mẫu.
- Bổ sung giao thức runtime cho agent thật: discovery contract, heartbeat, task heartbeat, callback hoàn tất task.
- Hỗ trợ cả 2 luồng sync và async cho agent runtime.
- Thêm tài liệu `docs/developer/AGENT_RUNTIME_CONTRACT.md`.
- Thêm agent Nmap tách riêng tại `agents/nmap-agent`.
- Agent Nmap hỗ trợ `mock` mode và `real` mode, callback heartbeat/status/normalize ngược về backend.
- Thêm `systemd` service và hướng dẫn deploy cho agent Nmap.
- Bổ sung auth RBAC cơ bản theo nhóm tài khoản: login, token, nhóm tài khoản, tài khoản, phân quyền theo nhóm.
- Frontend có màn đăng nhập, quản lý quyền theo nhóm, menu cấp 1/cấp 2 lọc theo permission.
- Bổ sung `mock demo flow` để launch operation + worker trong một bước.

### Trạng thái tạm thời

- Có thể dev tiếp từ local, chưa phụ thuộc bắt buộc vào internet.
- Chưa phải mọi lượt đều có verify runtime đầy đủ frontend/backend.

### Bước tiếp theo lúc đó

1. Chạy mock demo flow trực tiếp trong browser.
2. Test `agents/nmap-agent` trên Kali/VM khi máy đủ tài nguyên.
3. Thêm export PDF.

## 2026-04-28

### Cập nhật UI, dữ liệu nền và historical import

- Tinh gọn sidebar thành menu accordion, chỉ mở một menu cấp 1 tại một thời điểm.
- Khi đổi menu và đổi view, panel bên phải tự focus lên đầu.
- Thêm import CVE từ file Excel STMNC, map:
  - `Mã`
  - `Mức độ`
  - `Nguy cơ mất ATTT`
  - `Kiến nghị, đề xuất`
  - `Kiểm chứng`
- Mở rộng `vulnerability` để lưu `poc_text` và `poc_file_name`.
- Thêm kho script PoC tại `backend/data/poc_repository`.
- Mở rộng cụm `Mục tiêu`:
  - `Target`
  - `Target Attribute`
  - `Target Group`
  - import `Excel/CSV`, tự sinh attribute mới theo cột mới
- Bổ sung sort cho các bảng danh sách UI.
- Chuẩn hóa `Dải IP`:
  - hỗ trợ nhiều dải/IP cách nhau bởi dấu phẩy
  - tự chuẩn hóa pattern `[1 - 3]`, `[1_3]` về `[1-3]`
  - thêm hàm phân giải dải IP để phục vụ map scan result
- Đổi theme UI sang xanh lá cây đậm, nội dung nền kem xương.
- Nhập dữ liệu STMNC vào database:
  - seed CVE từ workbook mã lỗi
  - seed Target từ workbook target
  - gán toàn bộ target vào `Target Group` tên `TRTA2`
- Khởi động Phase 1 import scan cũ:
  - thêm backend import `services_vulns.csv` với `preview` và `commit`
  - hỗ trợ carry forward IP, tách nhiều vuln code bằng `;`, lookup theo `Vulnerability.code`
  - map IP vào tập target đã chọn, cho phép manual override hoặc `unmapped`
  - lưu metadata đợt import và tạo `operation_execution` / `task_execution` tương ứng
  - thêm UI `Import Scan Cũ`
- Làm lại cụm `CVE` và `Finding`:
  - title của `CVE` và `Finding` đồng bộ theo `code` / `finding_code`
  - thêm `note` cho finding và dời dữ liệu cũ từ `evidence` sang `note`
  - giữ `evidence` trống cho output hoặc file PoC tương lai
  - thêm upload / download / preview file PoC cho từng finding
  - file script thực thi PoC lưu ở `data/poc_repository`
  - file đính kèm / kết quả PoC của finding lưu ở `data/finding_poc_files`
- Khởi động Phase 2 dashboard:
  - API dashboard theo tuần / tháng / quý / năm
  - thẻ tổng quan theo thời gian và tổng hợp toàn thời gian
  - biểu đồ so sánh vuln theo quý cho tối đa 5 target
  - top 5 vuln/CVE theo bộ lọc thời gian
  - nhóm trọng điểm `ĐV Cấp 1` cho số lượng vuln và tỷ lệ target có nguy cơ
  - xu hướng vuln theo quý
- Cải thiện UX dashboard:
  - popup và drawer chọn target/nhóm trọng điểm
  - footer cố định cho drawer chọn nhiều mục
  - overlay toàn màn hình
  - gom nhóm thẻ biểu đồ, đổi bố cục nhiều lần để phù hợp demo
- Chuyển metadata `year / quarter / week / note / source_root_path / selected_target_ids` sang `operation_execution`.
- Điều chỉnh historical import để coi đây là kết quả execution thật của agent import.
- Bổ sung giao diện chọn target và metadata khi launch execution.
- Đổi task import nội bộ sang `internal://historical_scan_importer`.
- Đổi nhãn menu `Executions` thành `Operation Executions`.
- Làm lại module `Finding` theo workflow analyst:
  - severity và mô tả derive từ `Vulnerability.level` / `Vulnerability.threat`
  - thay CRUD generic `/scan-findings` bằng API chuyên dụng
  - upload PoC tự chuyển `confirmed`
  - xóa PoC tự chuyển `open`
  - bộ status analyst:
    - `open`
    - `confirmed`
    - `in_progress`
    - `resolved`
    - `false_positive`
    - `risk_accepted`
    - `reopened`
  - cho phép đổi trạng thái trực tiếp ngay trên danh sách finding
- Tách scroll sidebar và main panel độc lập trên desktop để tránh kéo lệch màn hình.

## 2026-05-05

### Cập nhật agent hệ thống và task xác minh vuln

- Đổi `System Import Agent` thành `System Agent`:
  - `code`: `AG-SYSTEM-01`
  - `name`: `System Agent`
  - `agent_type`: `system`
- Đổi task import scan lịch sử:
  - từ `Historical services_vulns.csv Import`
  - thành `P.K.T Scanner Result Import`
- Chuẩn hóa internal path của task import:
  - từ `internal://services_vulns_importer`
  - thành `internal://historical_scan_importer`
- Đồng bộ luồng historical import sang agent type `system`, không còn dùng `historical_import`.
- Bổ sung migration `009__rename_system_agent_and_add_verifier_agent.sql`.

### Bổ sung Vulnerability Verifier Agent

- Thêm agent mới:
  - `code`: `AG-VULN-VERIFY-01`
  - `name`: `Vulnerability Verifier Agent`
  - `agent_type`: `vulnerability_verifier`
- Thêm task mới:
  - `code`: `TASK-VULNERABILITY-VERIFY`
  - `name`: `Vulnerability Verifying`
- Gắn task xác minh vào cuối operation mẫu `OP-INTERNAL-WEEKLY`.
- Khóa logic `agent_type` của task theo agent ở backend:
  - task không còn coi `agent_type` là dữ liệu nhập tự do
  - create/update task sẽ map `agent_type` từ agent được chọn
- Điều chỉnh lại đúng mô hình nghiệp vụ của `Task`:
  - UI không còn chọn `agent_id`
  - UI chọn `agent_type` từ danh sách type agent hiện có trong hệ thống
  - một task có thể được nhiều agent cùng loại thực thi ở các máy khác nhau

### Runtime xác minh finding bằng PoC

- Thêm service `backend/app/services/vulnerability_verifier.py` để:
  - tìm finding thuộc `operation_execution_id` có trạng thái `open` hoặc `in_progress`
  - tạo thư mục chạy tạm trong `backend/data/verifier_runs`
  - copy script PoC của CVE vào thư mục tạm rồi thực thi
  - xóa script PoC sau khi chạy xong, nhưng giữ file PoC sinh ra
- Logic xử lý:
  - có script PoC:
    - mã `200`: upload file PoC sinh ra và chuyển finding sang `confirmed`
    - mã `201`: chuyển sang `false_positive`
    - mã `500/501/502`: giữ nguyên trạng thái finding
  - không có script nhưng có `PoC dạng text/ghi chú`:
    - tạo file `.txt` từ nội dung text PoC
    - gắn file này vào finding
    - chuyển finding sang `risk_accepted`
  - không có script và cũng không có text PoC:
    - chuyển finding sang `in_progress`
- Thêm runner `backend/app/services/agents/vulnerability_verifier/runner.py`.
- Worker chỉ normalize scan result với agent có parser; task verifier không còn bị ép parse như scan task.

### Chuẩn hóa script PoC mẫu

- Viết lại `backend/database/seed_sources/snmp-info-poc.py` theo chuẩn mới:
  - input: tên file PoC cần sinh ra
  - input môi trường: `HLT_TARGET_IP`
  - output code:
    - `200`: thành công và có file PoC
    - `201`: cảnh báo giả
    - `500`: lỗi không xác định hoặc thiếu input cần thiết
    - `501`: thiếu thư viện
    - `502`: thiếu công cụ
- Đồng bộ script này sang file nguồn STMNC để user tiếp tục sử dụng ngoài hệ thống.

### Dữ liệu thực và seed runtime

- Chạy lại `seed_data.py` trên MySQL thật để cập nhật:
  - `AG-SYSTEM-01`
  - `AG-VULN-VERIFY-01`
  - `P.K.T Scanner Result Import`
  - `Vulnerability Verifying`
  - nội dung script PoC `snmp-info`
- Backend compile pass sau toàn bộ thay đổi.

## 2026-05-06

### Bổ sung PKT Scanning cho agent Nmap

- Phân tích và gộp logic từ `scannerv2.sh` và `extractv2.py` thành script Python mới:
  - `data/agent_task_scripts/nmap/pkt_scannerv1.py`
- Script mới nhận:
  - danh sách IP / dải IP
  - tên thư mục lưu kết quả
  - thư mục gốc để ghi output
- Script mới:
  - tự khử trùng lặp đầu vào trước khi quét
  - tạo và giữ lại toàn bộ file trung gian phục vụ đối soát
  - xuất JSON kết quả scan trực tiếp thay vì sinh `services_vulns.csv`
  - trả về `result_code` và `message` để backend ghi nhận vào `task execution`
- Chuẩn mã kết quả bước scan:
  - `200`: thành công
  - `400`: đầu vào không hợp lệ
  - `404`: thiếu `nmap`
  - `501`: không tạo được thư mục output
  - `502`: lệnh quét thất bại
  - `503`: parse kết quả thất bại
  - `500`: lỗi không xác định

### Thêm task và operation cho luồng threat hunting

- Thêm trường `max_concurrency_per_agent` cho `Task`.
- Tạo task mới:
  - `TASK-PKT-SCANNING`
  - tên hiển thị: `PKT Scanning`
  - `agent_type`: `nmap`
  - `max_concurrency_per_agent = 1`
- Tạo operation mới:
  - `OP-PKT-THREAT-HUNTING`
  - tên hiển thị: `PKT Threat Hunting`
- Thứ tự task trong operation:
  1. `PKT Scanning`
  2. `Vulnerability Verifying`

### Nạp trực tiếp kết quả scan vào runtime

- Thêm service `backend/app/services/pkt_scanner_results.py` để:
  - sinh tên thư mục scan từ operation + metadata execution
  - mở rộng danh sách target thành danh sách IP / dải IP cần quét
  - nạp JSON output của `pkt_scannerv1.py` vào `scan_result`
  - tạo `scan_result_finding` tương ứng theo `Vulnerability.code`
  - tạo placeholder cho target được chọn nhưng không phát hiện IP public
  - giữ ghi chú cho trường hợp target trùng dải IP
- Điều chỉnh worker để:
  - tôn trọng giới hạn concurrency theo agent cho `PKT Scanning`
  - ingest trực tiếp output scan khi task `TASK-PKT-SCANNING` hoàn tất

### Điều chỉnh seed và UI quản lý task

- Cập nhật `seed_data.py` để seed:
  - task `PKT Scanning`
  - operation `PKT Threat Hunting`
  - script `pkt_scannerv1.py`
- Màn `Quản lý Task` hiển thị và cho sửa `max_concurrency_per_agent`.
- `.gitignore` được mở rộng thêm thư mục runtime:
  - `HLT-vkl-26/data/agent_runs/`

### Tự tạo CVE stub khi kết quả scan có mã mới

- Bổ sung hành vi tự tạo `Vulnerability` khi:
  - import `services_vulns.csv`
  - ingest kết quả `PKT Scanning`
  - normalize kết quả scan từ agent khác
- Record CVE mới được tạo theo chuẩn:
  - `code = mã vuln/CVE mới`
  - `title = mã vuln/CVE mới`
  - `level = 0`
  - các trường khác để trống
- Chuẩn mức `0` được đổi ý nghĩa từ `Thông tin` sang `Chưa xác định`.

## 2026-05-11

### Nâng cấp quản lý và giám sát Agent

- Mở rộng dữ liệu `Agent` với các trường:
  - `duration`
  - `old_time`
  - `old_status`
  - `status_note`
- Bổ sung migration `011__extend_agent_monitoring.sql`.
- Đồng bộ schema API để trả thêm thông tin thời lượng và trạng thái runtime của agent.

### Module kiểm tra trạng thái Agent theo chu kỳ 1 phút

- Thêm service `backend/app/services/agent_monitoring.py`.
- Bổ sung vòng lặp nền `AgentMonitorLoop` chạy theo `AGENT_MONITOR_POLL_SECONDS`.
- Logic trạng thái:
  - `offline`: không kết nối được, ghi chú `Đang thử kết nối lại...`
  - `ready`: agent sẵn sàng, ghi chú `Sẵn sàng`
  - `working`: agent đang thực thi, ghi chú tên operation và task
  - `error`: agent đang có lỗi, giữ lại ghi chú lỗi
- Trạng thái agent được tính tiếp từ `old_time` và `old_status`, nên không mất mạch duration khi server restart.

### UI giám sát Agent mới

- Tách menu `Agents` sang màn riêng `AgentManagementView.vue`.
- Bổ sung:
  - thẻ tổng quan số lượng agent và số lượng theo từng loại agent
  - grid card cho từng agent
  - bảng danh sách rút gọn phía dưới
  - thẻ `Thông tin Agent` không cho sửa `status`
- Các card agent:
  - sắp xếp theo `Ready`, `Working`, `Error`, `Offline`
  - cùng trạng thái thì ưu tiên `system` trước
  - cùng loại agent dùng cùng một tông màu nền
- Khi lưu thông tin agent, backend sẽ chủ động kích hoạt monitor nếu chưa sát chu kỳ kế tiếp.


## 2026-05-12

### Bổ sung tài liệu contract cho script

- Thêm `docs/developer/POC_SCRIPT_CONTRACT.md`:
  - mô tả chuẩn đầu vào/đầu ra cho PoC script
  - mã kết quả `200/201/500/501/502`
  - quy ước lưu script PoC, file PoC và file tạm trên agent
- Thêm `docs/developer/TASK_SCRIPT_CONTRACT.md`:
  - mô tả chuẩn cho các task script do agent thực thi
  - payload input, JSON output, artifact scan, `result_code`
  - quy tắc ingest scan result và xử lý CVE stub khi phát hiện mã mới
