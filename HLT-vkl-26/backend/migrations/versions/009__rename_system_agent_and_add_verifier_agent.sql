UPDATE agent
SET
    code = 'AG-SYSTEM-01',
    name = 'System Agent',
    agent_type = 'system'
WHERE code = 'AG-SYSTEM-IMPORT';

UPDATE task
SET
    name = 'P.K.T Scanner Result Import',
    agent_type = 'system'
WHERE code = 'TASK-HIST-SERVICES-VULNS-IMPORT';

UPDATE scan_result
SET agent_type = 'system'
WHERE agent_type = 'historical_import';

INSERT INTO agent (code, name, agent_type, host, ip_address, port, version, status, created_at, updated_at)
SELECT
    'AG-VULN-VERIFY-01',
    'Vulnerability Verifier Agent',
    'vulnerability_verifier',
    'localhost',
    '127.0.0.1',
    8091,
    '1.0.0',
    'online',
    UTC_TIMESTAMP(),
    UTC_TIMESTAMP()
WHERE NOT EXISTS (
    SELECT 1 FROM agent WHERE code = 'AG-VULN-VERIFY-01'
);

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
    is_active,
    created_at,
    updated_at
)
SELECT
    'TASK-VULNERABILITY-VERIFY',
    'Vulnerability Verifying',
    'vulnerability_verifier',
    'verify_findings.py',
    '/opt/hlt/tasks/verify_findings.py',
    NULL,
    JSON_OBJECT('operation_execution_id', 'integer'),
    JSON_OBJECT('verified_count', 'integer', 'items', 'array'),
    'Xac minh finding bang script PoC hoac text PoC cua CVE.',
    '1.0.0',
    TRUE,
    UTC_TIMESTAMP(),
    UTC_TIMESTAMP()
WHERE NOT EXISTS (
    SELECT 1 FROM task WHERE code = 'TASK-VULNERABILITY-VERIFY'
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
    3,
    JSON_OBJECT('mode', 'verify-findings'),
    TRUE,
    UTC_TIMESTAMP()
FROM operation
JOIN task ON task.code = 'TASK-VULNERABILITY-VERIFY'
WHERE operation.code = 'OP-INTERNAL-WEEKLY'
  AND NOT EXISTS (
      SELECT 1
      FROM operation_task
      WHERE operation_task.operation_id = operation.id
        AND operation_task.task_id = task.id
  );
