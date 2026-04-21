# Nmap Agent Demo

Agent nay duoc tach rieng khoi backend chinh de de copy sang may Kali hoac VM khac. Muc tieu la demo luong agent that:

- backend goi `POST /execute`
- agent nhan task va tra `accepted`
- agent tu callback heartbeat/status/normalize nguoc ve backend

## Cau truc

- `main.py`: FastAPI service cua agent.
- `app/backend_client.py`: goi callback ve backend.
- `app/nmap_executor.py`: chay `nmap` that hoac mock mode.
- `deploy/hlt-nmap-agent-demo.service`: mau `systemd` cho Kali/Linux.

## Che do chay

- `NMAP_AGENT_MODE=mock`: khong can cai `nmap`, tra XML mau de test luong end-to-end.
- `NMAP_AGENT_MODE=real`: agent se goi binary `nmap` that.

## Chuan bi tren Kali

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

## Cau hinh `.env`

Gia tri toi thieu can sua:

- `BACKEND_BASE_URL`: URL backend HLT, vi du `http://192.168.56.10:8000`
- `AGENT_CODE`: phai trung voi `agent.code` trong backend, mac dinh seed la `AG-NMAP-01`
- `AGENT_PORT`: cong agent se listen, mac dinh `8081`
- `AGENT_PUBLIC_HOST` hoac `AGENT_PUBLIC_IP`: thong tin de backend cap nhat heartbeat
- `NMAP_AGENT_MODE`: `mock` hoac `real`

Neu muon backend map dung agent theo seed mau, trong backend phan `agent` can de:

- `host` hoac `ip_address`: tro toi may Kali
- `port`: trung voi `AGENT_PORT`
- `agent_type`: `nmap`

## Chay local

```bash
cd /opt/hlt/nmap-agent-demo
source .venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8081
```

Kiem tra nhanh:

```bash
curl http://127.0.0.1:8081/health
```

## Dang ky systemd

```bash
sudo cp deploy/hlt-nmap-agent-demo.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now hlt-nmap-agent-demo
sudo systemctl status hlt-nmap-agent-demo
```

## Ghi chu runtime

- Agent hien uu tien luong async de demo callback day du.
- Neu `target.id` co gia tri, agent se tu goi endpoint normalize sau khi hoan tat.
- Trong `real` mode, command duoc build tu `input_data`:
  - `ports`
  - `timing`
  - `extra_args`

## Luong test nhanh

1. Backend HLT chay voi scheduler/worker hoac launch operation bang UI.
2. Ban ghi `agent` trong backend tro dung toi may Kali dang chay service nay.
3. Worker backend dispatch sang agent.
4. Agent callback ve backend va sinh `scan_result`, `scan_result_finding`.
