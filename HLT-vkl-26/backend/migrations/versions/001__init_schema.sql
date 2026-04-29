CREATE TABLE IF NOT EXISTS agent (
    id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    agent_type VARCHAR(100) NOT NULL,
    host VARCHAR(255) NULL,
    ip_address VARCHAR(64) NULL,
    port INT NULL,
    version VARCHAR(50) NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'offline',
    last_seen_at DATETIME NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS agent_capability (
    id INT AUTO_INCREMENT PRIMARY KEY,
    agent_id INT NOT NULL,
    capability_code VARCHAR(100) NOT NULL,
    capability_name VARCHAR(255) NOT NULL,
    metadata_json JSON NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_agent_capability_agent FOREIGN KEY (agent_id) REFERENCES agent(id)
);

CREATE TABLE IF NOT EXISTS agent_update_package (
    id INT AUTO_INCREMENT PRIMARY KEY,
    agent_type VARCHAR(100) NOT NULL,
    package_name VARCHAR(255) NOT NULL,
    package_version VARCHAR(50) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    checksum VARCHAR(255) NULL,
    description TEXT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS agent_update_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    agent_id INT NOT NULL,
    update_package_id INT NOT NULL,
    old_version VARCHAR(50) NULL,
    new_version VARCHAR(50) NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'pending',
    executed_at DATETIME NULL,
    note TEXT NULL,
    CONSTRAINT fk_agent_update_history_agent FOREIGN KEY (agent_id) REFERENCES agent(id),
    CONSTRAINT fk_agent_update_history_package FOREIGN KEY (update_package_id) REFERENCES agent_update_package(id)
);

CREATE TABLE IF NOT EXISTS task (
    id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    agent_type VARCHAR(100) NOT NULL,
    script_name VARCHAR(255) NULL,
    script_path VARCHAR(500) NULL,
    script_content LONGTEXT NULL,
    input_schema_json JSON NULL,
    output_schema_json JSON NULL,
    description TEXT NULL,
    version VARCHAR(50) NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS operation (
    id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    description TEXT NULL,
    schedule_type VARCHAR(30) NOT NULL DEFAULT 'none',
    schedule_config_json JSON NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS operation_task (
    id INT AUTO_INCREMENT PRIMARY KEY,
    operation_id INT NOT NULL,
    task_id INT NOT NULL,
    order_index INT NOT NULL DEFAULT 0,
    input_override_json JSON NULL,
    continue_on_error BOOLEAN NOT NULL DEFAULT FALSE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_operation_task_operation FOREIGN KEY (operation_id) REFERENCES operation(id),
    CONSTRAINT fk_operation_task_task FOREIGN KEY (task_id) REFERENCES task(id)
);

CREATE TABLE IF NOT EXISTS operation_execution (
    id INT AUTO_INCREMENT PRIMARY KEY,
    operation_id INT NOT NULL,
    execution_code VARCHAR(100) NOT NULL UNIQUE,
    trigger_type VARCHAR(30) NOT NULL DEFAULT 'manual',
    status VARCHAR(30) NOT NULL DEFAULT 'pending',
    started_at DATETIME NULL,
    finished_at DATETIME NULL,
    summary_json JSON NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_operation_execution_operation FOREIGN KEY (operation_id) REFERENCES operation(id)
);

CREATE TABLE IF NOT EXISTS target (
    id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    target_type VARCHAR(50) NOT NULL DEFAULT 'network',
    ip_range VARCHAR(255) NULL,
    domain VARCHAR(255) NULL,
    description TEXT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS target_attribute_definition (
    id INT AUTO_INCREMENT PRIMARY KEY,
    attribute_code VARCHAR(50) NOT NULL UNIQUE,
    attribute_name VARCHAR(255) NOT NULL,
    data_type VARCHAR(30) NOT NULL DEFAULT 'text',
    is_required BOOLEAN NOT NULL DEFAULT FALSE,
    default_value TEXT NULL,
    description TEXT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS target_attribute_value (
    id INT AUTO_INCREMENT PRIMARY KEY,
    target_id INT NOT NULL,
    attribute_definition_id INT NOT NULL,
    value_text TEXT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_target_attribute_value_target FOREIGN KEY (target_id) REFERENCES target(id),
    CONSTRAINT fk_target_attribute_value_definition FOREIGN KEY (attribute_definition_id) REFERENCES target_attribute_definition(id)
);

CREATE TABLE IF NOT EXISTS target_group (
    id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    description TEXT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS target_group_mapping (
    id INT AUTO_INCREMENT PRIMARY KEY,
    target_id INT NOT NULL,
    target_group_id INT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_target_group_mapping_target FOREIGN KEY (target_id) REFERENCES target(id),
    CONSTRAINT fk_target_group_mapping_group FOREIGN KEY (target_group_id) REFERENCES target_group(id)
);

CREATE TABLE IF NOT EXISTS vulnerability (
    id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(100) NOT NULL UNIQUE,
    title VARCHAR(255) NOT NULL,
    level INT NOT NULL DEFAULT 0,
    threat TEXT NULL,
    proposal TEXT NULL,
    poc_file_name VARCHAR(255) NULL,
    poc_text TEXT NULL,
    description TEXT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS vulnerability_reference (
    id INT AUTO_INCREMENT PRIMARY KEY,
    vulnerability_id INT NOT NULL,
    ref_type VARCHAR(50) NOT NULL,
    ref_value VARCHAR(255) NOT NULL,
    url VARCHAR(500) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_vulnerability_reference_vulnerability FOREIGN KEY (vulnerability_id) REFERENCES vulnerability(id)
);

CREATE TABLE IF NOT EXISTS vulnerability_script (
    id INT AUTO_INCREMENT PRIMARY KEY,
    vulnerability_id INT NOT NULL,
    script_name VARCHAR(255) NOT NULL,
    script_type VARCHAR(30) NOT NULL DEFAULT 'py',
    script_content LONGTEXT NOT NULL,
    version VARCHAR(50) NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_vulnerability_script_vulnerability FOREIGN KEY (vulnerability_id) REFERENCES vulnerability(id)
);

CREATE TABLE IF NOT EXISTS task_execution (
    id INT AUTO_INCREMENT PRIMARY KEY,
    operation_execution_id INT NOT NULL,
    operation_task_id INT NOT NULL,
    task_id INT NOT NULL,
    agent_id INT NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'pending',
    input_data_json JSON NULL,
    output_data_json JSON NULL,
    raw_log LONGTEXT NULL,
    started_at DATETIME NULL,
    finished_at DATETIME NULL,
    CONSTRAINT fk_task_execution_operation_execution FOREIGN KEY (operation_execution_id) REFERENCES operation_execution(id),
    CONSTRAINT fk_task_execution_operation_task FOREIGN KEY (operation_task_id) REFERENCES operation_task(id),
    CONSTRAINT fk_task_execution_task FOREIGN KEY (task_id) REFERENCES task(id),
    CONSTRAINT fk_task_execution_agent FOREIGN KEY (agent_id) REFERENCES agent(id)
);

CREATE TABLE IF NOT EXISTS scan_result (
    id INT AUTO_INCREMENT PRIMARY KEY,
    operation_execution_id INT NOT NULL,
    task_execution_id INT NOT NULL,
    target_id INT NOT NULL,
    agent_type VARCHAR(100) NOT NULL,
    source_tool VARCHAR(100) NULL,
    raw_output LONGTEXT NULL,
    normalized_output_json JSON NULL,
    detected_at DATETIME NULL,
    parse_status VARCHAR(30) NOT NULL DEFAULT 'success',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_scan_result_operation_execution FOREIGN KEY (operation_execution_id) REFERENCES operation_execution(id),
    CONSTRAINT fk_scan_result_task_execution FOREIGN KEY (task_execution_id) REFERENCES task_execution(id),
    CONSTRAINT fk_scan_result_target FOREIGN KEY (target_id) REFERENCES target(id)
);

CREATE TABLE IF NOT EXISTS scan_result_finding (
    id INT AUTO_INCREMENT PRIMARY KEY,
    scan_result_id INT NOT NULL,
    vulnerability_id INT NULL,
    finding_code VARCHAR(100) NOT NULL,
    severity VARCHAR(30) NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT NULL,
    port INT NULL,
    protocol VARCHAR(20) NULL,
    service_name VARCHAR(100) NULL,
    note TEXT NULL,
    evidence TEXT NULL,
    poc_file_name VARCHAR(255) NULL,
    poc_file_path VARCHAR(500) NULL,
    poc_file_mime_type VARCHAR(100) NULL,
    poc_file_size INT NULL,
    confidence INT NULL,
    first_seen_at DATETIME NULL,
    last_seen_at DATETIME NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'open',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_scan_result_finding_scan_result FOREIGN KEY (scan_result_id) REFERENCES scan_result(id),
    CONSTRAINT fk_scan_result_finding_vulnerability FOREIGN KEY (vulnerability_id) REFERENCES vulnerability(id)
);

CREATE TABLE IF NOT EXISTS finding_asset (
    id INT AUTO_INCREMENT PRIMARY KEY,
    scan_result_finding_id INT NOT NULL,
    target_id INT NULL,
    asset_type VARCHAR(50) NOT NULL,
    asset_value VARCHAR(255) NOT NULL,
    metadata_json JSON NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_finding_asset_finding FOREIGN KEY (scan_result_finding_id) REFERENCES scan_result_finding(id),
    CONSTRAINT fk_finding_asset_target FOREIGN KEY (target_id) REFERENCES target(id)
);

CREATE TABLE IF NOT EXISTS operation_result_import_export (
    id INT AUTO_INCREMENT PRIMARY KEY,
    operation_id INT NOT NULL,
    action_type VARCHAR(30) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NULL,
    file_format VARCHAR(30) NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'pending',
    executed_at DATETIME NULL,
    note TEXT NULL,
    CONSTRAINT fk_operation_result_import_export_operation FOREIGN KEY (operation_id) REFERENCES operation(id)
);

CREATE TABLE IF NOT EXISTS report_template (
    id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    report_type VARCHAR(50) NOT NULL,
    filter_config_json JSON NULL,
    layout_config_json JSON NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS generated_report (
    id INT AUTO_INCREMENT PRIMARY KEY,
    report_template_id INT NOT NULL,
    operation_execution_id INT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NULL,
    generated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    generated_by VARCHAR(100) NULL,
    summary_json JSON NULL,
    CONSTRAINT fk_generated_report_report_template FOREIGN KEY (report_template_id) REFERENCES report_template(id),
    CONSTRAINT fk_generated_report_operation_execution FOREIGN KEY (operation_execution_id) REFERENCES operation_execution(id)
);

CREATE TABLE IF NOT EXISTS report_snapshot (
    id INT AUTO_INCREMENT PRIMARY KEY,
    generated_report_id INT NOT NULL,
    snapshot_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    data_json JSON NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_report_snapshot_generated_report FOREIGN KEY (generated_report_id) REFERENCES generated_report(id)
);
