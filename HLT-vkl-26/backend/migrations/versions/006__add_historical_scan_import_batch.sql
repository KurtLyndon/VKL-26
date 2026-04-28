CREATE TABLE IF NOT EXISTS scan_import_batch (
    id INT AUTO_INCREMENT PRIMARY KEY,
    operation_execution_id INT NOT NULL,
    task_execution_id INT NOT NULL,
    batch_code VARCHAR(100) NOT NULL,
    scan_year INT NOT NULL,
    scan_quarter INT NOT NULL,
    scan_week INT NOT NULL,
    scan_started_at DATETIME NULL,
    scan_finished_at DATETIME NULL,
    note TEXT NULL,
    source_root_path VARCHAR(500) NULL,
    source_file_name VARCHAR(255) NOT NULL,
    selected_target_ids_json JSON NULL,
    summary_json JSON NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX ix_scan_import_batch_operation_execution_id (operation_execution_id),
    INDEX ix_scan_import_batch_task_execution_id (task_execution_id),
    INDEX ix_scan_import_batch_batch_code (batch_code),
    INDEX ix_scan_import_batch_scan_period (scan_year, scan_quarter, scan_week),
    CONSTRAINT fk_scan_import_batch_operation_execution
        FOREIGN KEY (operation_execution_id) REFERENCES operation_execution(id),
    CONSTRAINT fk_scan_import_batch_task_execution
        FOREIGN KEY (task_execution_id) REFERENCES task_execution(id)
);
