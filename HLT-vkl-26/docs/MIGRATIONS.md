# Migrations

## Muc tieu

- Co version cho schema va sample seed local.
- Khong can internet hoac scaffold tool ben ngoai.
- Chuyen duoc database cu sang luong versioned ma khong chen trung du lieu.

## Cau truc

- `backend/migrations/versions`: migration SQL canon.
- `backend/database/migrations.py`: migration engine va baseline stamping.
- `backend/scripts/migrate.py`: CLI local.
- `schema_migrations`: bang luu version da apply.

## Cach dung

```powershell
cd D:\Projects\VKL-26\HLT\HLT-vkl-26\backend
python scripts\migrate.py status
python scripts\migrate.py upgrade
```

## Baseline cho database cu

Neu database da duoc khoi tao bang `backend/database/*.sql` hoac `Base.metadata.create_all(...)`, runner se:

1. Tao bang `schema_migrations` neu chua co.
2. Kiem tra schema hien tai da co day du cac bang cot loi chua.
3. Stamp `001` neu schema baseline da ton tai.
4. Stamp `002` neu sample seed baseline da ton tai.

Nho do team co the chuyen sang migration versioned ma khong bi apply lai seed.

## Them migration moi

1. Tao file moi trong `backend/migrations/versions`.
2. Dung ten tang dan, vi du `003__add_scan_indexes.sql`.
3. Viet SQL cho chuyen doi moi.
4. Chay `python scripts\migrate.py upgrade`.
5. Cap nhat README/docs neu doi quy trinh local setup.

## Auto apply luc startup

Mac dinh app se fail som neu schema chua dung version. Neu muon local startup tu apply migration pending:

```powershell
$env:AUTO_APPLY_MIGRATIONS="true"
uvicorn app.main:app --reload
```

## Snapshot SQL cu

- `backend/database/001_init_schema.sql`
- `backend/database/002_seed_sample_data.sql`

Hai file nay duoc giu lai de tham khao hoac bootstrap thu cong. Nguon su that de phat trien schema tu bay gio la thu muc migration versioned.
