UPDATE target
SET target_type = 'web'
WHERE code IN (
    'TGT-INTERNET-ZERO-WEBAPPSECURITY',
    'TGT-INTERNET-TESTFIRE',
    'TGT-INTERNET-VULNWEB-ASP',
    'TGT-INTERNET-SCANME-NMAP',
    'TGT-INTERNET-ITSECGAMES',
    'TGT-INTERNET-JUICE-SHOP',
    'TGT-INTERNET-GOOGLE-GRUYERE'
);

UPDATE task
SET input_schema_json = JSON_OBJECT(
        'scan_entries', 'array: IP ranges, domains, or URLs',
        'folder_name', 'string',
        'selected_target_ids', 'array'
    ),
    description = 'Chay PKT scanner voi IP range, domain hoac URL; tong hop ket qua Nmap va nap truc tiep vao scan_result/finding.'
WHERE code = 'TASK-PKT-SCANNING';
