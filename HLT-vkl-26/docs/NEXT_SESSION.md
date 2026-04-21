# Next Session

## Muc tieu uu tien

- Deploy `agents/nmap-agent-demo` len Kali/VM va test luong end-to-end.
- Viet migration `003+` neu schema tiep tuc thay doi.
- Them auth va export PDF.

## Cach tiep tuc nhanh

1. Mo project `D:\Projects\VKL-26\HLT\HLT-vkl-26`.
2. Doc `docs/WORKLOG.md`.
3. Neu co MySQL local, vao `backend` roi chay `python scripts\migrate.py status` va `python scripts\migrate.py upgrade`.
4. Neu muon app local tu apply migration luc startup, bat `AUTO_APPLY_MIGRATIONS=true`.
5. Vao `agents/nmap-agent-demo`, copy `.env.example` thanh `.env` va sua `BACKEND_BASE_URL`.
6. Chay agent bang `uvicorn main:app --host 0.0.0.0 --port 8081` tren Kali/VM.
7. Sau do uu tien export PDF, auth va migration tiep theo.
