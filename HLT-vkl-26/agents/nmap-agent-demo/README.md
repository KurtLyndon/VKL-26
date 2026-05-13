# HLT Nmap Agent

Agent nay duoc dong goi de chay tren Kali/VM va nhan cac task `agent_type=nmap` tu HLT.

## Task Ho Tro

- `TASK-NMAP-TCP`: chay `nmap`, tra XML, va goi normalize callback ve backend.
- `TASK-PKT-SCANNING`: chay `task_scripts/nmap/pkt_scannerv1.py`, gui raw JSON ve task status callback de backend ingest vao `scan_result` va `scan_result_finding`.

## Cau Truc

- `main.py`: FastAPI service, expose `/health`, `/runs`, `/execute`.
- `app/backend_client.py`: callback heartbeat/status/normalize ve backend HLT.
- `app/nmap_executor.py`: build command va chay nmap/PKT scanner.
- `task_scripts/nmap/pkt_scannerv1.py`: script PKT scanner duoc copy vao image.
- `Dockerfile`: image cai san Python runtime va `nmap`.

## Cau Hinh `.env`

Sua file `.env` trong thu muc agent truoc khi chay:

```env
BACKEND_BASE_URL=http://<ip-may-HLT>:8000
AGENT_PUBLIC_IP=<ip-may-Kali-hoac-VM-agent>
AGENT_CODE=AG-NMAP-01
NMAP_AGENT_MODE=real
```

Bien quan trong:

- `BACKEND_BASE_URL`: URL backend HLT.
- `AGENT_CODE`: phai trung voi `agent.code` trong backend, seed mac dinh la `AG-NMAP-01`.
- `AGENT_PORT`: cong agent listen, mac dinh `8081`.
- `AGENT_PUBLIC_HOST` / `AGENT_PUBLIC_IP`: dia chi agent de backend cap nhat heartbeat.
- `NMAP_AGENT_MODE`: `mock` hoac `real`.
- `PKT_SCANNER_OUTPUT_ROOT`: thu muc luu output PKT trong container.

## Build Va Export Docker Image

```bash
cd agents/nmap-agent-demo
docker build -t hlt-nmap-agent:0.2.0 .
docker save hlt-nmap-agent:0.2.0 -o hlt-nmap-agent-0.2.0.tar
```

Hoac chay script:

```bash
./build-export.sh
```

Tren Windows PowerShell:

```powershell
.\build-export.ps1
```

Copy file `hlt-nmap-agent-0.2.0.tar` sang Kali, sau do:

```bash
docker load -i hlt-nmap-agent-0.2.0.tar
docker run --rm --network host --env-file .env hlt-nmap-agent:0.2.0
```

Neu khong dung `--network host`:

```bash
docker run --rm -p 8081:8081 --env-file .env hlt-nmap-agent:0.2.0
```

Kiem tra:

```bash
curl http://127.0.0.1:8081/health
```

## Chay Khong Docker

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --host 0.0.0.0 --port 8081
```

## Luu Y HLT

Trong backend, ban ghi agent can co:

- `agent_type`: `nmap`
- `code`: trung voi `AGENT_CODE`
- `host` hoac `ip_address`: tro den Kali/VM agent
- `port`: trung voi `AGENT_PORT`

Backend dispatch qua `POST /execute`; agent se callback heartbeat/status ve cac path trong contract.
