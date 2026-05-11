SET @agent_duration_exists := (
    SELECT COUNT(*)
    FROM information_schema.columns
    WHERE table_schema = DATABASE()
      AND table_name = 'agent'
      AND column_name = 'duration'
);

SET @agent_duration_ddl := IF(
    @agent_duration_exists = 0,
    'ALTER TABLE agent ADD COLUMN duration INT NOT NULL DEFAULT 0 AFTER status',
    'SELECT 1'
);

PREPARE stmt FROM @agent_duration_ddl;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @agent_old_time_exists := (
    SELECT COUNT(*)
    FROM information_schema.columns
    WHERE table_schema = DATABASE()
      AND table_name = 'agent'
      AND column_name = 'old_time'
);

SET @agent_old_time_ddl := IF(
    @agent_old_time_exists = 0,
    'ALTER TABLE agent ADD COLUMN old_time DATETIME NULL AFTER duration',
    'SELECT 1'
);

PREPARE stmt FROM @agent_old_time_ddl;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @agent_old_status_exists := (
    SELECT COUNT(*)
    FROM information_schema.columns
    WHERE table_schema = DATABASE()
      AND table_name = 'agent'
      AND column_name = 'old_status'
);

SET @agent_old_status_ddl := IF(
    @agent_old_status_exists = 0,
    'ALTER TABLE agent ADD COLUMN old_status VARCHAR(30) NULL AFTER old_time',
    'SELECT 1'
);

PREPARE stmt FROM @agent_old_status_ddl;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @agent_status_note_exists := (
    SELECT COUNT(*)
    FROM information_schema.columns
    WHERE table_schema = DATABASE()
      AND table_name = 'agent'
      AND column_name = 'status_note'
);

SET @agent_status_note_ddl := IF(
    @agent_status_note_exists = 0,
    'ALTER TABLE agent ADD COLUMN status_note TEXT NULL AFTER old_status',
    'SELECT 1'
);

PREPARE stmt FROM @agent_status_note_ddl;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
