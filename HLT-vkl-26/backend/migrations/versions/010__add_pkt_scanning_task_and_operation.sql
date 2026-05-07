SET @task_max_concurrency_exists := (
    SELECT COUNT(*)
    FROM information_schema.columns
    WHERE table_schema = DATABASE()
      AND table_name = 'task'
      AND column_name = 'max_concurrency_per_agent'
);

SET @task_max_concurrency_ddl := IF(
    @task_max_concurrency_exists = 0,
    'ALTER TABLE task ADD COLUMN max_concurrency_per_agent INT NOT NULL DEFAULT 0 AFTER version',
    'SELECT 1'
);

PREPARE stmt FROM @task_max_concurrency_ddl;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

INSERT INTO task (
    code,
    name,
    agent_type,
    script_name,
    script_path,
    script_content,
    input_schema_json,
    output_schema_json,
    description,
    version,
    max_concurrency_per_agent,
    is_active,
    created_at,
    updated_at
)
SELECT
    'TASK-PKT-SCANNING',
    'PKT Scanning',
    'nmap',
    'pkt_scannerv1.py',
    'data/agent_task_scripts/nmap/pkt_scannerv1.py',
    NULL,
    JSON_OBJECT(
        'scan_entries', 'array',
        'folder_name', 'string',
        'selected_target_ids', 'array'
    ),
    JSON_OBJECT(
        'result_code', 'integer',
        'folder_name', 'string',
        'output_dir', 'string',
        'scan_results', 'array',
        'warnings', 'array'
    ),
    'Chay PKT scanner, tong hop ket qua Nmap va nap truc tiep vao scan_result/finding.',
    '1.0.0',
    1,
    TRUE,
    UTC_TIMESTAMP(),
    UTC_TIMESTAMP()
WHERE NOT EXISTS (
    SELECT 1 FROM task WHERE code = 'TASK-PKT-SCANNING'
);

INSERT INTO operation (
    code,
    name,
    description,
    schedule_type,
    schedule_config_json,
    is_active,
    created_at,
    updated_at
)
SELECT
    'OP-PKT-THREAT-HUNTING',
    'PKT Threat Hunting',
    'Operation P.K.T gom buoc scan va xac minh finding.',
    'none',
    NULL,
    TRUE,
    UTC_TIMESTAMP(),
    UTC_TIMESTAMP()
WHERE NOT EXISTS (
    SELECT 1 FROM operation WHERE code = 'OP-PKT-THREAT-HUNTING'
);

INSERT INTO operation_task (
    operation_id,
    task_id,
    order_index,
    input_override_json,
    continue_on_error,
    created_at
)
SELECT
    operation.id,
    task.id,
    1,
    JSON_OBJECT('mode', 'pkt-scan'),
    FALSE,
    UTC_TIMESTAMP()
FROM operation
JOIN task ON task.code = 'TASK-PKT-SCANNING'
WHERE operation.code = 'OP-PKT-THREAT-HUNTING'
  AND NOT EXISTS (
      SELECT 1
      FROM operation_task
      WHERE operation_task.operation_id = operation.id
        AND operation_task.task_id = task.id
  );

INSERT INTO operation_task (
    operation_id,
    task_id,
    order_index,
    input_override_json,
    continue_on_error,
    created_at
)
SELECT
    operation.id,
    task.id,
    2,
    JSON_OBJECT('mode', 'verify-findings'),
    TRUE,
    UTC_TIMESTAMP()
FROM operation
JOIN task ON task.code = 'TASK-VULNERABILITY-VERIFY'
WHERE operation.code = 'OP-PKT-THREAT-HUNTING'
  AND NOT EXISTS (
      SELECT 1
      FROM operation_task
      WHERE operation_task.operation_id = operation.id
        AND operation_task.task_id = task.id
  );
