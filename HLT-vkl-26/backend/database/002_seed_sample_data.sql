USE hlt_vkl_26;

INSERT INTO agent (code, name, agent_type, host, ip_address, port, version, status)
VALUES
    ('AG-NMAP-01', 'Nmap Agent 01', 'nmap', 'agent-nmap-01', '192.168.10.21', 8081, '1.0.0', 'online'),
    ('AG-NUCLEI-01', 'Nuclei Agent 01', 'nuclei', 'agent-nuclei-01', '192.168.10.22', 8082, '1.0.0', 'online');

INSERT INTO task (code, name, agent_type, script_name, script_path, description, version, is_active, input_schema_json, output_schema_json)
VALUES
    (
        'TASK-NMAP-TCP',
        'TCP Port Discovery',
        'nmap',
        'tcp_scan.py',
        '/opt/hlt/tasks/tcp_scan.py',
        'Quet port TCP co ban cho target network.',
        '1.0.0',
        TRUE,
        JSON_OBJECT('target', 'cidr', 'ports', 'string'),
        JSON_OBJECT('hosts', 'array', 'ports', 'array')
    ),
    (
        'TASK-NUCLEI-WEB',
        'Web Vulnerability Discovery',
        'nuclei',
        'web_vuln.py',
        '/opt/hlt/tasks/web_vuln.py',
        'Quet template nuclei cho web target.',
        '1.0.0',
        TRUE,
        JSON_OBJECT('target', 'url', 'templates', 'array'),
        JSON_OBJECT('findings', 'array')
    );

INSERT INTO operation (code, name, description, schedule_type, schedule_config_json, is_active)
VALUES
    (
        'OP-INTERNAL-WEEKLY',
        'Weekly Internal Assessment',
        'Operation mau cho kiem thu dinh ky he thong noi bo.',
        'cron',
        JSON_OBJECT('expression', '0 1 * * 1'),
        TRUE
    );

INSERT INTO operation_task (operation_id, task_id, order_index, input_override_json, continue_on_error)
VALUES
    (1, 1, 1, JSON_OBJECT('ports', '1-1024'), FALSE),
    (1, 2, 2, JSON_OBJECT('templates', JSON_ARRAY('cves', 'default-logins')), TRUE);

INSERT INTO report_template (code, name, report_type, filter_config_json, layout_config_json)
VALUES
    (
        'RPT-WEEKLY-SUMMARY',
        'Weekly Security Summary',
        'weekly',
        JSON_OBJECT('severity', JSON_ARRAY('critical', 'high', 'medium')),
        JSON_OBJECT('sections', JSON_ARRAY('overview', 'findings', 'targets'))
    );
