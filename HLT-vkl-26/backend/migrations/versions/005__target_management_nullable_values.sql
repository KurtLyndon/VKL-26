SET @column_nullable := (
    SELECT IS_NULLABLE
    FROM information_schema.columns
    WHERE table_schema = DATABASE()
      AND table_name = 'target_attribute_value'
      AND column_name = 'value_text'
    LIMIT 1
);

SET @ddl := IF(
    @column_nullable = 'NO',
    'ALTER TABLE target_attribute_value MODIFY COLUMN value_text TEXT NULL',
    'SELECT 1'
);

PREPARE stmt FROM @ddl;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
