CREATE TABLE IF NOT EXISTS account_group (
    id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    description TEXT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS app_permission (
    id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(100) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    module_name VARCHAR(100) NOT NULL,
    description TEXT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS account_group_permission (
    id INT AUTO_INCREMENT PRIMARY KEY,
    group_id INT NOT NULL,
    permission_id INT NOT NULL,
    is_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_account_group_permission_group FOREIGN KEY (group_id) REFERENCES account_group(id),
    CONSTRAINT fk_account_group_permission_permission FOREIGN KEY (permission_id) REFERENCES app_permission(id),
    CONSTRAINT uq_account_group_permission UNIQUE (group_id, permission_id)
);

CREATE TABLE IF NOT EXISTS user_account (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(80) NOT NULL UNIQUE,
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NULL,
    password_hash VARCHAR(255) NOT NULL,
    group_id INT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    last_login_at DATETIME NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_user_account_group FOREIGN KEY (group_id) REFERENCES account_group(id)
);

INSERT INTO account_group (code, name, description, is_active)
VALUES
    ('ADMIN', 'Administrators', 'Toan quyen quan tri he thong.', TRUE),
    ('ANALYST', 'Security Analysts', 'Nhom van hanh va theo doi ket qua scan.', TRUE)
ON DUPLICATE KEY UPDATE
    name = VALUES(name),
    description = VALUES(description),
    is_active = VALUES(is_active);

INSERT INTO app_permission (code, name, module_name, description)
VALUES
    ('dashboard.view', 'View Dashboard', 'dashboard', 'Xem dashboard tong quan.'),
    ('agents.manage', 'Manage Agents', 'agents', 'Quan ly agent va trang thai agent.'),
    ('tasks.manage', 'Manage Tasks', 'tasks', 'Quan ly task va workflow task.'),
    ('operations.manage', 'Manage Operations', 'operations', 'Quan ly operation va operation task.'),
    ('runtime.control', 'Control Runtime', 'runtime', 'Launch operation, chay scheduler, worker va mock flow.'),
    ('targets.manage', 'Manage Targets', 'targets', 'Quan ly target va target group.'),
    ('vulnerabilities.manage', 'Manage Vulnerabilities', 'vulnerabilities', 'Quan ly CVE, PoC va script.'),
    ('scan_results.view', 'View Scan Results', 'scan', 'Xem scan result va finding.'),
    ('reports.manage', 'Manage Reports', 'reports', 'Import export va quan ly bao cao.'),
    ('auth.manage', 'Manage Auth', 'auth', 'Quan ly nhom tai khoan, tai khoan va phan quyen.')
ON DUPLICATE KEY UPDATE
    name = VALUES(name),
    module_name = VALUES(module_name),
    description = VALUES(description);

INSERT INTO account_group_permission (group_id, permission_id, is_enabled)
SELECT g.id, p.id, TRUE
FROM account_group g
JOIN app_permission p
WHERE g.code = 'ADMIN'
ON DUPLICATE KEY UPDATE is_enabled = VALUES(is_enabled);

INSERT INTO account_group_permission (group_id, permission_id, is_enabled)
SELECT g.id, p.id, TRUE
FROM account_group g
JOIN app_permission p
WHERE g.code = 'ANALYST'
  AND p.code IN (
    'dashboard.view',
    'runtime.control',
    'scan_results.view',
    'reports.manage'
  )
ON DUPLICATE KEY UPDATE is_enabled = VALUES(is_enabled);

INSERT INTO user_account (username, full_name, email, password_hash, group_id, is_active)
SELECT
    'admin',
    'System Administrator',
    'admin@hlt.local',
    'pbkdf2_sha256$120000$729e4ed967aa4cd2$kxCaDtq5kafvIbsw6NLZHIhx3Lkc38WMrxh+1DAxYx4=',
    g.id,
    TRUE
FROM account_group g
WHERE g.code = 'ADMIN'
ON DUPLICATE KEY UPDATE
    full_name = VALUES(full_name),
    email = VALUES(email),
    group_id = VALUES(group_id),
    is_active = VALUES(is_active);
