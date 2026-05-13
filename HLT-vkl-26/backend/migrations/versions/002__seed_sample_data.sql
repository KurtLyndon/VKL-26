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

INSERT INTO target (code, name, target_type, ip_range, domain, description)
VALUES
    ('TGT-DC-NET', 'Domain Controller Segment', 'network', '192.168.10.0/24', NULL, 'Mang noi bo chua cac may chu dich vu quan trong.'),
    ('TGT-PORTAL', 'Internal Portal', 'web', NULL, 'portal.internal.local', 'Cong thong tin noi bo.');

INSERT INTO target_attribute_definition (attribute_code, attribute_name, data_type, is_required, default_value, description)
VALUES
    ('business_unit', 'Business Unit', 'text', FALSE, NULL, 'Don vi so huu target'),
    ('criticality', 'Criticality', 'text', FALSE, 'medium', 'Muc do quan trong cua tai san');

INSERT INTO target_attribute_value (target_id, attribute_definition_id, value_text)
VALUES
    (1, 1, 'Infrastructure'),
    (1, 2, 'high'),
    (2, 1, 'Corporate IT'),
    (2, 2, 'medium');

INSERT INTO target_group (code, name, description)
VALUES
    ('GRP-CORE', 'Core Systems', 'Nhom he thong can uu tien theo doi'),
    ('GRP-INTERNET-TEST-TARGETS', 'Internet Test Targets', 'Public intentionally vulnerable or scan-permitted targets for security testing.');

INSERT INTO target_group_mapping (target_id, target_group_id)
VALUES
    (1, 1),
    (2, 1);

INSERT INTO target (code, name, target_type, ip_range, domain, description)
VALUES
    ('TGT-INTERNET-ZERO-WEBAPPSECURITY', 'Zero WebAppSecurity', 'web', NULL, 'http://zero.webappsecurity.com/', 'Public vulnerable banking demo site for authorized web security testing.'),
    ('TGT-INTERNET-TESTFIRE', 'Altoro Mutual Testfire', 'web', NULL, 'https://demo.testfire.net/', 'Public vulnerable web application demo for authorized web security testing.'),
    ('TGT-INTERNET-VULNWEB-ASP', 'VulnWeb TestASP', 'web', NULL, 'http://testasp.vulnweb.com/', 'Public Acunetix VulnWeb ASP test application.'),
    ('TGT-INTERNET-SCANME-NMAP', 'Nmap ScanMe', 'web', NULL, 'http://scanme.nmap.org/', 'Public host provided by Nmap for permitted scanner testing.'),
    ('TGT-INTERNET-ITSECGAMES', 'ITSec Games', 'web', NULL, 'http://www.itsecgames.com/index.htm', 'Public web security training target.'),
    ('TGT-INTERNET-JUICE-SHOP', 'OWASP Juice Shop', 'web', NULL, 'https://juice-shop.github.io/', 'OWASP Juice Shop public project/demo entry point for web security testing.'),
    ('TGT-INTERNET-GOOGLE-GRUYERE', 'Google Gruyere', 'web', NULL, 'https://google-gruyere.appspot.com/start', 'Google Gruyere vulnerable web application for web security testing.');

INSERT INTO target_group_mapping (target_id, target_group_id)
SELECT target.id, target_group.id
FROM target
JOIN target_group ON target_group.code = 'GRP-INTERNET-TEST-TARGETS'
WHERE target.code IN (
    'TGT-INTERNET-ZERO-WEBAPPSECURITY',
    'TGT-INTERNET-TESTFIRE',
    'TGT-INTERNET-VULNWEB-ASP',
    'TGT-INTERNET-SCANME-NMAP',
    'TGT-INTERNET-ITSECGAMES',
    'TGT-INTERNET-JUICE-SHOP',
    'TGT-INTERNET-GOOGLE-GRUYERE'
);

INSERT INTO vulnerability (code, title, level, threat, proposal, poc_file_name, description)
VALUES
    (
        'CVE-2024-DEMO-0001',
        'Demo Internal RCE',
        4,
        'Co the dan den thuc thi lenh tu xa tren dich vu noi bo.',
        'Cap nhat ban va han che truy cap den dich vu quan tri.',
        'demo_rce_check.py',
        'Ban ghi mau de dev giao dien va quy trinh quan ly CVE.'
    );

INSERT INTO vulnerability_script (vulnerability_id, script_name, script_type, script_content, version, is_active)
VALUES
    (
        1,
        'demo_rce_check.py',
        'py',
        'print("safe poc placeholder")',
        '1.0.0',
        TRUE
    );

INSERT INTO report_template (code, name, report_type, filter_config_json, layout_config_json)
VALUES
    (
        'RPT-WEEKLY-SUMMARY',
        'Weekly Security Summary',
        'weekly',
        JSON_OBJECT('severity', JSON_ARRAY('critical', 'high', 'medium')),
        JSON_OBJECT('sections', JSON_ARRAY('overview', 'findings', 'targets'))
    );
