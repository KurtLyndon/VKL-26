# Agent Runtime Contract

Tài liệu này mô tả contract runtime tối thiểu mà backend hiện hỗ trợ cho external agent.

## Execute Dispatch

- Backend gọi `POST /execute` trên external agent.
- Request body bám theo `AgentExecuteRequest`.
- Response body bám theo `AgentExecuteResponse`.

### Các trường trong request

- `contract_version`: phiên bản contract hiện tại.
- `dispatched_at`: thời điểm UTC khi backend gửi request.
- `task_execution_id`: ID task execution của backend.
- `operation_execution_id`: ID operation execution của backend.
- `agent`: metadata của agent record được chọn bên backend.
- `task`: metadata của task, gồm `code`, `script_name`, `script_path`, và version.
- `target`: metadata của target đã resolve, kèm trường `value` đã chuẩn hóa.
- `input_data`: dữ liệu input đã merge từ shared input và operation-task override.
- `callback_paths`: các callback path về backend cho heartbeat, completion, và normalize scan result nếu cần.

### Các mode response

- Hoàn tất đồng bộ:
  - Trả `status="completed"` và có `raw_output`.
  - Backend sẽ đánh dấu task hoàn tất và normalize finding ngay.
- Chấp nhận bất đồng bộ:
  - Trả `status="accepted"` hoặc `status="running"`.
  - Backend giữ task ở trạng thái `running` và chờ các callback tiếp theo.

## Heartbeat Callbacks

### `POST /api/v1/agents/heartbeat`

Dùng endpoint này để refresh trạng thái sống của agent.

- Bắt buộc có: `agent_id` hoặc `agent_code`
- Payload thường dùng:
  - `status="online"`
  - `version`, `host`, `ip_address`, `port`
  - `seen_at`

Endpoint này sẽ cập nhật `agent.status` và `agent.last_seen_at`.

### `POST /api/v1/task-executions/{task_execution_id}/heartbeat`

Dùng endpoint này khi task đã được dispatch nhưng vẫn đang chạy.

- Có thể kèm agent guard: `agent_id` hoặc `agent_code`
- Status hỗ trợ: `queued`, `running`
- Trường tiến độ tùy chọn:
  - `progress_percent`
  - `raw_log`
  - `output_data_json`

Endpoint này sẽ refresh cả trạng thái sống của agent lẫn runtime state của task execution.

## Completion Callback

### `POST /api/v1/task-executions/{task_execution_id}/status`

Dùng task status API hiện có để kết thúc task.

- `status`: `running`, `completed`, `failed`, hoặc `canceled`
- `output_data_json`: output có cấu trúc ở thời điểm cuối
- `raw_log`: log hoặc lỗi ở thời điểm cuối

Nếu task hoàn tất thành công và external agent chưa trả `raw_output` inline từ đầu, agent có thể gọi normalize scan result ở bước tiếp theo.

## Optional Normalize Callback

### `POST /api/v1/scan-results/normalize`

Dùng endpoint này khi agent muốn backend parser chuẩn hóa raw scan output sau khi hoàn tất bất đồng bộ.

Các trường bắt buộc:

- `agent_type`
- `raw_output`
- `operation_execution_id`
- `task_execution_id`
- `target_id`

## Discovery Endpoint

Backend expose `GET /api/v1/agents/runtime/execute-contract` để trả về phiên bản contract hiện tại cùng ví dụ request/response payload.
