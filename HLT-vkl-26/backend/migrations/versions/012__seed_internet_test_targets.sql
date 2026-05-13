INSERT INTO target_group (code, name, description, created_at)
SELECT
    'GRP-INTERNET-TEST-TARGETS',
    'Internet Test Targets',
    'Public intentionally vulnerable or scan-permitted targets for security testing.',
    UTC_TIMESTAMP()
WHERE NOT EXISTS (
    SELECT 1 FROM target_group WHERE code = 'GRP-INTERNET-TEST-TARGETS'
);

INSERT INTO target (code, name, target_type, ip_range, domain, description, created_at, updated_at)
SELECT
    seed.code,
    seed.name,
    'web',
    NULL,
    seed.domain,
    seed.description,
    UTC_TIMESTAMP(),
    UTC_TIMESTAMP()
FROM (
    SELECT 'TGT-INTERNET-ZERO-WEBAPPSECURITY' AS code, 'Zero WebAppSecurity' AS name, 'http://zero.webappsecurity.com/' AS domain, 'Public vulnerable banking demo site for authorized web security testing.' AS description
    UNION ALL SELECT 'TGT-INTERNET-TESTFIRE', 'Altoro Mutual Testfire', 'https://demo.testfire.net/', 'Public vulnerable web application demo for authorized web security testing.'
    UNION ALL SELECT 'TGT-INTERNET-VULNWEB-ASP', 'VulnWeb TestASP', 'http://testasp.vulnweb.com/', 'Public Acunetix VulnWeb ASP test application.'
    UNION ALL SELECT 'TGT-INTERNET-SCANME-NMAP', 'Nmap ScanMe', 'http://scanme.nmap.org/', 'Public host provided by Nmap for permitted scanner testing.'
    UNION ALL SELECT 'TGT-INTERNET-ITSECGAMES', 'ITSec Games', 'http://www.itsecgames.com/index.htm', 'Public web security training target.'
    UNION ALL SELECT 'TGT-INTERNET-JUICE-SHOP', 'OWASP Juice Shop', 'https://juice-shop.github.io/', 'OWASP Juice Shop public project/demo entry point for web security testing.'
    UNION ALL SELECT 'TGT-INTERNET-GOOGLE-GRUYERE', 'Google Gruyere', 'https://google-gruyere.appspot.com/start', 'Google Gruyere vulnerable web application for web security testing.'
) AS seed
WHERE NOT EXISTS (
    SELECT 1 FROM target WHERE target.code = seed.code
);

INSERT INTO target_group_mapping (target_id, target_group_id, created_at)
SELECT target.id, target_group.id, UTC_TIMESTAMP()
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
)
AND NOT EXISTS (
    SELECT 1
    FROM target_group_mapping existing
    WHERE existing.target_id = target.id
      AND existing.target_group_id = target_group.id
);
