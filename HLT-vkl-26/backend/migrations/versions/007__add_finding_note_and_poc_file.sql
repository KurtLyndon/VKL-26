ALTER TABLE scan_result_finding
    ADD COLUMN note TEXT NULL AFTER service_name,
    ADD COLUMN poc_file_name VARCHAR(255) NULL AFTER evidence,
    ADD COLUMN poc_file_path VARCHAR(500) NULL AFTER poc_file_name,
    ADD COLUMN poc_file_mime_type VARCHAR(100) NULL AFTER poc_file_path,
    ADD COLUMN poc_file_size INT NULL AFTER poc_file_mime_type;

UPDATE vulnerability
SET title = code
WHERE code IS NOT NULL
  AND title <> code;

UPDATE scan_result_finding
SET note = evidence
WHERE evidence IS NOT NULL
  AND (note IS NULL OR note = '');

UPDATE scan_result_finding
SET title = finding_code
WHERE finding_code IS NOT NULL
  AND title <> finding_code;

UPDATE scan_result_finding
SET evidence = NULL
WHERE evidence IS NOT NULL;
