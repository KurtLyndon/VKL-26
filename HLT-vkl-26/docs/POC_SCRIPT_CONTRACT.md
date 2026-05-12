# PoC Script Contract

Tài liệu này mô tả chuẩn đầu vào, đầu ra và quy ước lưu trữ cho các script PoC dùng để xác thực `Vulnerability` hoặc `Finding`.

## Mục tiêu

- Chuẩn hóa cách viết các script PoC trong tương lai.
- Giúp `Vulnerability Verifier Agent` gọi script theo một contract thống nhất.
- Giúp backend biết cách nhận file PoC sinh ra, cập nhật trạng thái finding, và lưu trữ bằng chứng.

## Khi nào dùng PoC script

PoC script được dùng khi một `Vulnerability` có khả năng kiểm chứng tự động bằng script.

Ví dụ:

- kiểm tra SNMP public info
- kiểm tra banner/service trả về tín hiệu xác thực lỗi
- tạo file text hoặc ảnh làm bằng chứng

Nếu một CVE chỉ có ghi chú dạng text, không cần PoC script; hệ thống sẽ tạo file `.txt` từ nội dung ghi chú đó.

## Nơi lưu trữ

### Script PoC nguồn

PoC script nguồn nên được lưu tại:

- `backend/data/poc_repository/<vulnerability-code>/`

Ví dụ:

- `backend/data/poc_repository/snmp-info/snmp-info-poc.py`

### File PoC sinh ra cho từng finding

File kết quả kiểm chứng của từng finding nên được lưu tại:

- `backend/data/finding_poc_files/finding-<finding-id>/`

Ví dụ:

- `backend/data/finding_poc_files/finding-128/snmp-info-128.txt`
- `backend/data/finding_poc_files/finding-256/http-proof.png`

### File tạm tại máy agent

Agent verifier có thể tạo thư mục tạm để chạy script và sinh file trung gian, ví dụ:

- `data/verifier_runs/<task-execution-id>/`

Khi hoàn tất:

- xóa script PoC đã copy xuống máy agent
- giữ lại file PoC kết quả nếu cần upload ngược về server

## Đầu vào chuẩn

PoC script nên nhận đầu vào tối thiểu như sau:

### Cách 1: đối số dòng lệnh

Khuyến nghị đơn giản nhất:

```bash
python poc-script.py "<output_file_name>"
```

Trong đó:

- `output_file_name`: tên file PoC mà script phải sinh ra tại thư mục đang thực thi

Ví dụ:

```bash
python snmp-info-poc.py "snmp-info-128.txt"
```

### Cách 2: có thêm đối số mở rộng

Nếu cần, script có thể nhận thêm:

- IP đích
- port
- protocol
- username/password/test token
- đường dẫn thư mục làm việc

Ví dụ:

```bash
python poc-script.py "<output_file_name>" "<target_ip>" "<target_port>"
```

## Đầu ra chuẩn

PoC script phải:

1. sinh ra một file PoC tại đúng thư mục đang thực thi
2. trả về một mã kết quả để agent hiểu và cập nhật finding

### Loại file PoC được chấp nhận

- `.txt`
- `.log`
- `.png`
- `.jpg`
- `.jpeg`
- `.rar`
- `.zip`

Khuyến nghị ưu tiên:

- text nếu là bằng chứng dạng thông báo
- png/jpg nếu là ảnh chụp màn hình

## Mã kết quả chuẩn

### `200`

Ý nghĩa:

- script chạy thành công
- đã xác thực được finding
- chắc chắn đã sinh ra file PoC

Hành vi hệ thống:

- upload file PoC về server
- gắn file đó vào finding
- chuyển trạng thái finding thành `confirmed`

### `201`

Ý nghĩa:

- script chạy thành công
- xác định đây là cảnh báo giả

Hành vi hệ thống:

- không bắt buộc phải có file PoC
- chuyển trạng thái finding thành `false_positive`

### `500`

Ý nghĩa:

- script không chạy được do lỗi không xác định

Hành vi hệ thống:

- giữ nguyên trạng thái finding
- ghi lỗi vào `status_note` hoặc log runtime

### `501`

Ý nghĩa:

- script không chạy được do thiếu thư viện

Ví dụ:

- thiếu package Python
- thiếu module hệ thống

Hành vi hệ thống:

- giữ nguyên trạng thái finding
- đánh dấu lỗi kỹ thuật để người vận hành xử lý

### `502`

Ý nghĩa:

- script không chạy được do thiếu công cụ

Ví dụ:

- thiếu `nmap`
- thiếu `snmpwalk`
- thiếu `curl`

Hành vi hệ thống:

- giữ nguyên trạng thái finding
- đánh dấu lỗi kỹ thuật để người vận hành xử lý

## Quy ước tên file PoC

Khuyến nghị backend hoặc agent chuẩn hóa tên file theo mẫu:

- `<finding-code>-<finding-id>.<ext>`

Ví dụ:

- `snmp-info-128.txt`
- `CVE-2026-0001-245.png`

Mục tiêu:

- dễ truy vết về finding
- tránh trùng tên file

## Quy tắc chuyển trạng thái finding

### Nếu CVE có PoC script

- chạy script
- cập nhật theo mã kết quả `200/201/500/501/502`

### Nếu CVE chỉ có `PoC dạng text / ghi chú`

- hệ thống tự tạo file `.txt` từ nội dung text đó
- gắn file này làm PoC của finding
- chuyển trạng thái finding thành `risk_accepted`

### Nếu CVE không có script và cũng không có PoC text

- chuyển trạng thái finding thành `in_progress`

## Khuyến nghị triển khai

- script nên tự ghi log ngắn gọn ra `stdout` hoặc `stderr`
- script không nên ghi file ra ngoài thư mục làm việc hiện tại
- script nên ưu tiên ASCII cho output text, trừ khi cần Unicode
- script nên fail sớm nếu thiếu dependency
- script nên có phần usage ngắn nếu thiếu tham số

## Ví dụ khung script Python tối thiểu

```python
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) < 2:
        return 500

    output_name = sys.argv[1]
    output_path = Path.cwd() / output_name
    output_path.write_text("PoC verification result\n", encoding="utf-8")
    return 200


if __name__ == "__main__":
    raise SystemExit(main())
```

## Ghi chú

- Contract này là chuẩn khuyến nghị cho HLT hiện tại.
- Nếu về sau cần thêm metadata đầu vào như `operation_execution_id`, `finding_id`, `target_ip`, nên mở rộng theo kiểu tương thích ngược, không phá vỡ cách gọi đơn giản hiện tại.
