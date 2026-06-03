SET @column_exists := (
    SELECT COUNT(*)
    FROM information_schema.columns
    WHERE table_schema = DATABASE()
      AND table_name = 'scan_result_finding'
      AND column_name = 'note'
);
SET @ddl := IF(
    @column_exists = 0,
    'ALTER TABLE scan_result_finding ADD COLUMN note TEXT NULL AFTER service_name',
    'SELECT 1'
);
PREPARE stmt FROM @ddl;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @column_exists := (
    SELECT COUNT(*)
    FROM information_schema.columns
    WHERE table_schema = DATABASE()
      AND table_name = 'scan_result_finding'
      AND column_name = 'evidence_file_name'
);
SET @ddl := IF(
    @column_exists = 0,
    'ALTER TABLE scan_result_finding ADD COLUMN evidence_file_name VARCHAR(255) NULL AFTER note',
    'SELECT 1'
);
PREPARE stmt FROM @ddl;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @column_exists := (
    SELECT COUNT(*)
    FROM information_schema.columns
    WHERE table_schema = DATABASE()
      AND table_name = 'scan_result_finding'
      AND column_name = 'evidence_file_path'
);
SET @ddl := IF(
    @column_exists = 0,
    'ALTER TABLE scan_result_finding ADD COLUMN evidence_file_path VARCHAR(500) NULL AFTER evidence_file_name',
    'SELECT 1'
);
PREPARE stmt FROM @ddl;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @column_exists := (
    SELECT COUNT(*)
    FROM information_schema.columns
    WHERE table_schema = DATABASE()
      AND table_name = 'scan_result_finding'
      AND column_name = 'evidence_file_mime_type'
);
SET @ddl := IF(
    @column_exists = 0,
    'ALTER TABLE scan_result_finding ADD COLUMN evidence_file_mime_type VARCHAR(100) NULL AFTER evidence_file_path',
    'SELECT 1'
);
PREPARE stmt FROM @ddl;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @column_exists := (
    SELECT COUNT(*)
    FROM information_schema.columns
    WHERE table_schema = DATABASE()
      AND table_name = 'scan_result_finding'
      AND column_name = 'evidence_file_size'
);
SET @ddl := IF(
    @column_exists = 0,
    'ALTER TABLE scan_result_finding ADD COLUMN evidence_file_size INT NULL AFTER evidence_file_mime_type',
    'SELECT 1'
);
PREPARE stmt FROM @ddl;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

UPDATE vulnerability
SET title = code
WHERE code IS NOT NULL
  AND title <> code;

UPDATE scan_result_finding
SET title = finding_code
WHERE finding_code IS NOT NULL
  AND title <> finding_code;
