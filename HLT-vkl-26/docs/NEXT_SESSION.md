# Next Session

## Mục tiêu ưu tiên

- Test browser thực tế cho login, RBAC và mock demo flow.
- Deploy `agents/nmap-agent-demo` lên Kali/VM khi máy đủ tài nguyên.
- Thêm export PDF.

## Cách tiếp tục nhanh

1. Mở project `D:\Projects\VKL-26\HLT\HLT-vkl-26`.
2. Đọc `docs/WORKLOG.md`.
3. Nếu có MySQL local, vào `backend` rồi chạy `python scripts\migrate.py status` và `python scripts\migrate.py upgrade`.
4. Nếu muốn app local tự apply migration lúc startup, bật `AUTO_APPLY_MIGRATIONS=true`.
5. Đăng nhập bằng `admin` / `Admin@123`.
6. Thử nút `Run Mock Demo` trong `Operation Control`.
7. Sau đó ưu tiên export PDF, rà soát UI và agent thật.
