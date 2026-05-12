# Task Script Contract

Tài liệu này mô tả chuẩn dành cho các script task do agent thực thi, ví dụ các script quét mạng, thu thập thông tin, hoặc nhập dữ liệu lịch sử vào runtime của hệ thống.

## Mục tiêu

- Chuẩn hóa cách viết script task cho nhiều loại agent khác nhau.
- Giúp agent runner biết cách truyền input và lấy output.
- Giúp backend ingest kết quả vào `operation_execution`, `task_execution`, `scan_result`, `scan_result_finding`.

## Phạm vi áp dụng

Contract này dùng cho các script task kiểu:

- `PKT Scanning`
- quét TCP/UDP
- quét service và mapping vuln
- các script scan nội bộ khác trong tương lai

Không áp dụng cho:

- PoC script xác minh CVE riêng lẻ
- logic `internal://...` chạy hoàn toàn trong backend

## Nơi lưu trữ

### Script task nguồn

Khuyến nghị lưu tập trung theo loại agent:

- `data/agent_scripts/<agent-type>/`

Ví dụ:

- `data/agent_scripts/nmap/pkt_scannerv1.py`
- `data/agent_scripts/nuclei/web_template_runner.py`

### Thư mục runtime tại máy agent

Mỗi lần thực thi task nên tạo thư mục riêng:

- `data/agent_runs/<task-execution-id>/`

Hoặc:

- `data/agent_runs/<operation-execution-id>/<task-execution-id>/`

Trong thư mục này có thể giữ:

- file input tạm
- file output tạm
- log
- artifact scan như:
  - `tcp_full.gnmap`
  - `tcp_full.nmap`
  - `tcp_full.xml`
  - `udpcore.gnmap`
  - `udpcore.nmap`
  - `udpcore.xml`
  - `alive_a.txt`
  - `alive_b.txt`
  - `discovery.gnmap`
  - `fallback.gnmap`
  - `hosts.txt`

## Đầu vào chuẩn

Task script nên nhận một payload logic gồm các nhóm dữ liệu sau.

### 1. Runtime metadata

- `operation_execution_id`
- `task_execution_id`
- `operation_code`
- `task_code`
- `year`
- `quarter`
- `week`
- `started_at`
- `source_root_path`

### 2. Danh sách mục tiêu

- `targets`: danh sách target đã chọn cho operation execution
- mỗi target nên có:
  - `target_id`
  - `target_name`
  - `ip_range`
  - `resolved_entries`

### 3. Input riêng của task

- `input_data`
- `shared_input`
- `task_override`

### 4. Thư mục làm việc

- `output_dir`

## Cách truyền input khuyến nghị

### Cách 1: truyền file JSON

Khuyến nghị nhất:

```bash
python task-script.py "<input_json_path>"
```

Trong đó file JSON chứa toàn bộ payload kể trên.

### Cách 2: truyền chuỗi JSON

Chỉ dùng nếu runner chủ động kiểm soát shell:

```bash
python task-script.py --payload-json "{...}"
```

### Cách 3: truyền đối số ngắn gọn

Chỉ phù hợp với script đơn giản:

```bash
python task-script.py "<targets>" "<output_dir>"
```

## Đầu ra chuẩn

Task script nên sinh ra một JSON result có cấu trúc thống nhất.

Ví dụ:

```json
{
  "result_code": 200,
  "status": "completed",
  "summary": {
    "targets_total": 10,
    "targets_scanned": 8,
    "targets_without_public_ip": 2,
    "open_ports": 56,
    "findings": 14
  },
  "artifacts": [
    "tcp_full.xml",
    "udpcore.xml",
    "hosts.txt"
  ],
  "scan_results": [
    {
      "ip": "192.168.1.10",
      "port": 80,
      "service": "http",
      "version": "Apache httpd 2.4.57",
      "vulns": ["CVE-2026-0001", "snmp-info"]
    }
  ],
  "warnings": [],
  "errors": []
}
```

## Ý nghĩa các trường đầu ra

- `result_code`: mã kết quả nghiệp vụ của script
- `status`: `completed`, `partial`, hoặc `failed`
- `summary`: thống kê ngắn gọn để đưa vào `summary_json`
- `artifacts`: danh sách file sinh ra trong thư mục scan
- `scan_results`: dữ liệu scan chuẩn hóa ở mức logic
- `warnings`: cảnh báo không làm hỏng toàn bộ tác vụ
- `errors`: lỗi cụ thể

## Mã kết quả chuẩn

### `200`

- chạy thành công
- output đầy đủ
- backend có thể ingest ngay

### `206`

- chạy thành công một phần
- vẫn có dữ liệu hợp lệ để ingest
- một số target hoặc bước nhỏ bị lỗi

### `400`

- input không hợp lệ

Ví dụ:

- thiếu danh sách target
- format payload sai

### `404`

- không tìm thấy file hoặc nguồn vào bắt buộc

Ví dụ:

- thiếu template
- thiếu file data đầu vào

### `409`

- xung đột runtime

Ví dụ:

- đã có một scan cùng loại đang giữ lock
- vi phạm giới hạn `max_concurrency_per_agent`

### `500`

- lỗi không xác định

### `501`

- thiếu thư viện

Ví dụ:

- thiếu package Python
- thiếu parser dependency

### `502`

- thiếu công cụ scan

Ví dụ:

- thiếu `nmap`
- thiếu `masscan`
- thiếu `snmpwalk`

## Quy ước exit code của process

Khuyến nghị:

- process exit code của hệ điều hành nên là `0` nếu script đã hoàn thành và sinh được JSON output hợp lệ
- mã lỗi nghiệp vụ nên nằm trong `result_code`

Lý do:

- agent runner dễ parse và quản lý hơn
- tránh nhầm giữa lỗi shell và lỗi nghiệp vụ

Nếu script chết trước khi sinh JSON hợp lệ:

- runner có thể coi là lỗi `500`

## Hành vi ingest vào backend

### Với script quét vuln/service

Backend hoặc agent runner nên:

1. đọc `scan_results`
2. map từng dòng sang `scan_result`
3. map từng mã vuln sang `scan_result_finding`
4. nếu vuln chưa tồn tại trong bảng `Vulnerability`, tự tạo record stub:
   - `code = mã vuln`
   - `title = mã vuln`
   - `level = 0`

### Với target được chọn nhưng không có IP public

Script hoặc runner nên tạo note:

- `Không phát hiện IP public`

### Với target trùng dải IP

Script hoặc runner nên tạo note:

- `Trùng dải IP với <tên mục tiêu trùng>`

## Quy tắc xử lý danh sách IP

Task script nên:

- loại bỏ IP trùng
- loại bỏ dải IP trùng
- chuẩn hóa format trước khi quét
- hỗ trợ:
  - IP đơn
  - CIDR
  - range
  - danh sách phân tách bằng dấu phẩy
  - dạng bracket như `[1-3]`

## Khuyến nghị thiết kế script

- tách phần scan, parse, export thành các hàm riêng
- ghi log rõ ràng vào thư mục output
- không ghi file ra ngoài `output_dir`
- giữ lại artifact scan để phục vụ điều tra và import lại nếu cần
- output JSON nên ổn định để backend dễ ingest

## Ví dụ luồng cho PKT Scanning

1. Nhận danh sách target đã chọn từ operation execution
2. Mở rộng thành danh sách IP / dải IP
3. Lọc trùng trước khi quét
4. Tạo thư mục scan theo tên operation + metadata
5. Sinh các file scan trung gian
6. Chuẩn hóa dữ liệu thành `scan_results`
7. Trả JSON result với `result_code = 200`
8. Backend ingest vào `scan_result` và `scan_result_finding`

## Ghi chú

- Contract này là chuẩn khuyến nghị cho các task script chạy bởi agent trong HLT.
- Nếu về sau cần thêm mode async hoặc callback trực tiếp từ script, nên mở rộng bằng trường mới trong JSON thay vì phá vỡ cấu trúc hiện tại.
