INSERT INTO app_permission (code, name, module_name, description)
VALUES
    ('database_explorer.view', 'View Database Explorer', 'database', 'Cho phep admin chay cau SELECT va xem cau truc database.')
ON DUPLICATE KEY UPDATE
    name = VALUES(name),
    module_name = VALUES(module_name),
    description = VALUES(description);

INSERT INTO account_group_permission (group_id, permission_id, is_enabled)
SELECT account_group.id, app_permission.id, TRUE
FROM account_group
JOIN app_permission ON app_permission.code = 'database_explorer.view'
WHERE account_group.code = 'ADMIN'
ON DUPLICATE KEY UPDATE is_enabled = VALUES(is_enabled);
