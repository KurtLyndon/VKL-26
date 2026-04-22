# Nmap Agent Demo

Agent này được tách riêng khỏi backend chính để dễ copy sang máy Kali hoặc VM khác. Mục tiêu là demo luồng agent thật:

- backend gọi `POST /execute`
- agent nhận task và trả `accepted`
- agent tự callback heartbeat/status/normalize ngược về backend

## Cấu trúc

- `main.py`: FastAPI service của agent.
- `app/backend_client.py`: gọi callback về backend.
- `app/nmap_executor.py`: chạy `nmap` thật hoặc mock mode.
- `deploy/hlt-nmap-agent-demo.service`: mẫu `systemd` cho Kali/Linux.

## Chế độ chạy

- `NMAP_AGENT_MODE=mock`: không cần cài `nmap`, trả XML mẫu để test luồng end-to-end.
- `NMAP_AGENT_MODE=real`: agent sẽ gọi binary `nmap` thật.

## Chuẩn bị trên Kali

```bash
sudo apt update
sudo apt install -y python3 python3-venv nmap
mkdir -p /opt/hlt
cp -r nmap-agent-demo /opt/hlt/
cd /opt/hlt/nmap-agent-demo
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## Cấu hình `.env`

Giá trị tối thiểu cần sửa:

- `BACKEND_BASE_URL`: URL backend HLT, ví dụ `http://192.168.56.10:8000`
- `AGENT_CODE`: phải trùng với `agent.code` trong backend, mặc định seed là `AG-NMAP-01`
- `AGENT_PORT`: cổng agent sẽ listen, mặc định `8081`
- `AGENT_PUBLIC_HOST` hoặc `AGENT_PUBLIC_IP`: thông tin để backend cập nhật heartbeat
- `NMAP_AGENT_MODE`: `mock` hoặc `real`

Nếu muốn backend map đúng agent theo seed mẫu, trong backend phần `agent` cần để:

- `host` hoặc `ip_address`: trỏ tới máy Kali
- `port`: trùng với `AGENT_PORT`
- `agent_type`: `nmap`

## Chạy Local

```bash
cd /opt/hlt/nmap-agent-demo
source .venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8081
```

Kiểm tra nhanh:

```bash
curl http://127.0.0.1:8081/health
```

## Đăng ký systemd

```bash
sudo cp deploy/hlt-nmap-agent-demo.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now hlt-nmap-agent-demo
sudo systemctl status hlt-nmap-agent-demo
```

## Ghi chú runtime

- Agent hiện ưu tiên luồng async để demo callback đầy đủ.
- Nếu `target.id` có giá trị, agent sẽ tự gọi endpoint normalize sau khi hoàn tất.
- Trong `real` mode, command được build từ `input_data`:
  - `ports`
  - `timing`
  - `extra_args`

## Luồng test nhanh

1. Backend HLT chạy với scheduler/worker hoặc launch operation bằng UI.
2. Bản ghi `agent` trong backend trỏ đúng tới máy Kali đang chạy service này.
3. Worker backend dispatch sang agent.
4. Agent callback về backend và sinh `scan_result`, `scan_result_finding`.
