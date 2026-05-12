# Migrations

## Mục tiêu

- Có version cho schema và sample seed local.
- Không cần internet hoặc scaffold tool bên ngoài.
- Chuyển được database cũ sang luồng versioned mà không chèn trùng dữ liệu.

## Cấu trúc

- `backend/migrations/versions`: migration SQL chuẩn.
- `backend/database/migrations.py`: migration engine và baseline stamping.
- `backend/scripts/migrate.py`: CLI local.
- `schema_migrations`: bảng lưu version đã apply.

## Cách dùng

```powershell
cd D:\Projects\VKL-26\HLT\HLT-vkl-26\backend
python scripts\migrate.py status
python scripts\migrate.py upgrade
```

## Baseline cho database cũ

Nếu database đã được khởi tạo bằng `backend/database/*.sql` hoặc `Base.metadata.create_all(...)`, runner sẽ:

1. Tạo bảng `schema_migrations` nếu chưa có.
2. Kiểm tra schema hiện tại đã có đầy đủ các bảng cốt lõi chưa.
3. Stamp `001` nếu schema baseline đã tồn tại.
4. Stamp `002` nếu sample seed baseline đã tồn tại.

Nhờ đó team có thể chuyển sang migration versioned mà không bị apply lại seed.

## Thêm migration mới

1. Tạo file mới trong `backend/migrations/versions`.
2. Dùng tên tăng dần, ví dụ `003__add_scan_indexes.sql`.
3. Viết SQL cho chuyển đổi mới.
4. Chạy `python scripts\migrate.py upgrade`.
5. Cập nhật README/docs nếu đổi quy trình local setup.

## Auto Apply Lúc Startup

Mặc định app sẽ fail sớm nếu schema chưa đúng version. Nếu muốn local startup tự apply migration pending:

```powershell
$env:AUTO_APPLY_MIGRATIONS="true"
uvicorn app.main:app --reload
```

## Snapshot SQL Cũ

- `backend/database/001_init_schema.sql`
- `backend/database/002_seed_sample_data.sql`

Hai file này được giữ lại để tham khảo hoặc bootstrap thủ công. Nguồn sự thật để phát triển schema từ bây giờ là thư mục migration versioned.
