SET @exists_poc_text := (
    SELECT COUNT(*)
    FROM information_schema.columns
    WHERE table_schema = DATABASE()
      AND table_name = 'vulnerability'
      AND column_name = 'poc_text'
);
SET @exists_evidence_text := (
    SELECT COUNT(*)
    FROM information_schema.columns
    WHERE table_schema = DATABASE()
      AND table_name = 'vulnerability'
      AND column_name = 'evidence_text'
);
SET @stmt := IF(
    @exists_poc_text > 0 AND @exists_evidence_text = 0,
    'ALTER TABLE vulnerability CHANGE COLUMN poc_text evidence_text TEXT NULL',
    IF(@exists_evidence_text = 0, 'ALTER TABLE vulnerability ADD COLUMN evidence_text TEXT NULL AFTER poc_file_name', 'SELECT 1')
);
PREPARE rename_stmt FROM @stmt;
EXECUTE rename_stmt;
DEALLOCATE PREPARE rename_stmt;

SET @exists_old := (
    SELECT COUNT(*)
    FROM information_schema.columns
    WHERE table_schema = DATABASE()
      AND table_name = 'scan_result_finding'
      AND column_name = 'evidence'
);
SET @exists_new := (
    SELECT COUNT(*)
    FROM information_schema.columns
    WHERE table_schema = DATABASE()
      AND table_name = 'scan_result_finding'
      AND column_name = 'runtime_output'
);
SET @stmt := IF(
    @exists_old > 0 AND @exists_new = 0,
    'ALTER TABLE scan_result_finding CHANGE COLUMN evidence runtime_output TEXT NULL',
    IF(@exists_new = 0, 'ALTER TABLE scan_result_finding ADD COLUMN runtime_output TEXT NULL AFTER note', 'SELECT 1')
);
PREPARE rename_stmt FROM @stmt;
EXECUTE rename_stmt;
DEALLOCATE PREPARE rename_stmt;

SET @exists_old := (
    SELECT COUNT(*)
    FROM information_schema.columns
    WHERE table_schema = DATABASE()
      AND table_name = 'scan_result_finding'
      AND column_name = 'poc_file_name'
);
SET @exists_new := (
    SELECT COUNT(*)
    FROM information_schema.columns
    WHERE table_schema = DATABASE()
      AND table_name = 'scan_result_finding'
      AND column_name = 'evidence_file_name'
);
SET @stmt := IF(
    @exists_old > 0 AND @exists_new = 0,
    'ALTER TABLE scan_result_finding CHANGE COLUMN poc_file_name evidence_file_name VARCHAR(255) NULL',
    IF(@exists_new = 0, 'ALTER TABLE scan_result_finding ADD COLUMN evidence_file_name VARCHAR(255) NULL AFTER runtime_output', 'SELECT 1')
);
PREPARE rename_stmt FROM @stmt;
EXECUTE rename_stmt;
DEALLOCATE PREPARE rename_stmt;

SET @exists_old := (
    SELECT COUNT(*)
    FROM information_schema.columns
    WHERE table_schema = DATABASE()
      AND table_name = 'scan_result_finding'
      AND column_name = 'poc_file_path'
);
SET @exists_new := (
    SELECT COUNT(*)
    FROM information_schema.columns
    WHERE table_schema = DATABASE()
      AND table_name = 'scan_result_finding'
      AND column_name = 'evidence_file_path'
);
SET @stmt := IF(
    @exists_old > 0 AND @exists_new = 0,
    'ALTER TABLE scan_result_finding CHANGE COLUMN poc_file_path evidence_file_path VARCHAR(500) NULL',
    IF(@exists_new = 0, 'ALTER TABLE scan_result_finding ADD COLUMN evidence_file_path VARCHAR(500) NULL AFTER evidence_file_name', 'SELECT 1')
);
PREPARE rename_stmt FROM @stmt;
EXECUTE rename_stmt;
DEALLOCATE PREPARE rename_stmt;

SET @exists_old := (
    SELECT COUNT(*)
    FROM information_schema.columns
    WHERE table_schema = DATABASE()
      AND table_name = 'scan_result_finding'
      AND column_name = 'poc_file_mime_type'
);
SET @exists_new := (
    SELECT COUNT(*)
    FROM information_schema.columns
    WHERE table_schema = DATABASE()
      AND table_name = 'scan_result_finding'
      AND column_name = 'evidence_file_mime_type'
);
SET @stmt := IF(
    @exists_old > 0 AND @exists_new = 0,
    'ALTER TABLE scan_result_finding CHANGE COLUMN poc_file_mime_type evidence_file_mime_type VARCHAR(100) NULL',
    IF(@exists_new = 0, 'ALTER TABLE scan_result_finding ADD COLUMN evidence_file_mime_type VARCHAR(100) NULL AFTER evidence_file_path', 'SELECT 1')
);
PREPARE rename_stmt FROM @stmt;
EXECUTE rename_stmt;
DEALLOCATE PREPARE rename_stmt;

SET @exists_old := (
    SELECT COUNT(*)
    FROM information_schema.columns
    WHERE table_schema = DATABASE()
      AND table_name = 'scan_result_finding'
      AND column_name = 'poc_file_size'
);
SET @exists_new := (
    SELECT COUNT(*)
    FROM information_schema.columns
    WHERE table_schema = DATABASE()
      AND table_name = 'scan_result_finding'
      AND column_name = 'evidence_file_size'
);
SET @stmt := IF(
    @exists_old > 0 AND @exists_new = 0,
    'ALTER TABLE scan_result_finding CHANGE COLUMN poc_file_size evidence_file_size INT NULL',
    IF(@exists_new = 0, 'ALTER TABLE scan_result_finding ADD COLUMN evidence_file_size INT NULL AFTER evidence_file_mime_type', 'SELECT 1')
);
PREPARE rename_stmt FROM @stmt;
EXECUTE rename_stmt;
DEALLOCATE PREPARE rename_stmt;
