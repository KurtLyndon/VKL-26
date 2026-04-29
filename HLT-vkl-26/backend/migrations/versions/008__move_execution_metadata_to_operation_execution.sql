ALTER TABLE operation_execution
    ADD COLUMN year INT NULL AFTER finished_at,
    ADD COLUMN quarter INT NULL AFTER year,
    ADD COLUMN week INT NULL AFTER quarter,
    ADD COLUMN note TEXT NULL AFTER week,
    ADD COLUMN source_root_path VARCHAR(500) NULL AFTER note,
    ADD COLUMN selected_target_ids_json JSON NULL AFTER source_root_path;

UPDATE operation_execution execution
JOIN scan_import_batch batch
  ON batch.operation_execution_id = execution.id
SET
    execution.year = COALESCE(execution.year, batch.scan_year),
    execution.quarter = COALESCE(execution.quarter, batch.scan_quarter),
    execution.week = COALESCE(execution.week, batch.scan_week),
    execution.note = COALESCE(execution.note, batch.note),
    execution.source_root_path = COALESCE(execution.source_root_path, batch.source_root_path),
    execution.selected_target_ids_json = COALESCE(execution.selected_target_ids_json, batch.selected_target_ids_json)
WHERE execution.year IS NULL
   OR execution.quarter IS NULL
   OR execution.week IS NULL
   OR execution.note IS NULL
   OR execution.source_root_path IS NULL
   OR execution.selected_target_ids_json IS NULL;
