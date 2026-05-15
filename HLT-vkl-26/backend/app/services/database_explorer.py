from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from re import IGNORECASE, search, sub
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.services.database_schema_metadata import build_schema_text_for_ai


FORBIDDEN_SQL_TOKENS = (
    "alter",
    "analyze",
    "call",
    "create",
    "delete",
    "drop",
    "execute",
    "grant",
    "insert",
    "into",
    "load",
    "lock",
    "optimize",
    "replace",
    "revoke",
    "set",
    "truncate",
    "update",
    "outfile",
    "dumpfile",
)


def _current_schema(db: Session) -> str:
    return str(db.execute(text("SELECT DATABASE()")).scalar() or "")


def get_database_schema(db: Session) -> dict[str, Any]:
    schema_name = _current_schema(db)
    column_rows = db.execute(
        text(
            """
            SELECT
                TABLE_NAME AS table_name,
                COLUMN_NAME AS column_name,
                COLUMN_TYPE AS column_type,
                IS_NULLABLE AS is_nullable,
                COLUMN_KEY AS column_key,
                COLUMN_DEFAULT AS column_default,
                EXTRA AS extra
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = :schema_name
            ORDER BY TABLE_NAME ASC, ORDINAL_POSITION ASC
            """
        ),
        {"schema_name": schema_name},
    ).mappings()

    tables: dict[str, dict[str, Any]] = {}
    for row in column_rows:
        table = tables.setdefault(
            row["table_name"],
            {"name": row["table_name"], "columns": [], "foreign_keys": []},
        )
        table["columns"].append(
            {
                "name": row["column_name"],
                "type": row["column_type"],
                "nullable": row["is_nullable"] == "YES",
                "key": row["column_key"] or None,
                "default": row["column_default"],
                "extra": row["extra"] or None,
            }
        )

    fk_rows = db.execute(
        text(
            """
            SELECT
                CONSTRAINT_NAME AS constraint_name,
                TABLE_NAME AS table_name,
                COLUMN_NAME AS column_name,
                REFERENCED_TABLE_NAME AS referenced_table_name,
                REFERENCED_COLUMN_NAME AS referenced_column_name
            FROM information_schema.KEY_COLUMN_USAGE
            WHERE TABLE_SCHEMA = :schema_name
              AND REFERENCED_TABLE_NAME IS NOT NULL
            ORDER BY TABLE_NAME ASC, COLUMN_NAME ASC
            """
        ),
        {"schema_name": schema_name},
    ).mappings()

    for row in fk_rows:
        table = tables.get(row["table_name"])
        if not table:
            continue
        table["foreign_keys"].append(
            {
                "constraint": row["constraint_name"],
                "column": row["column_name"],
                "references_table": row["referenced_table_name"],
                "references_column": row["referenced_column_name"],
            }
        )

    return {"schema": schema_name, "tables": list(tables.values())}


def get_database_schema_text(db: Session) -> dict[str, str]:
    schema_document = get_database_schema(db)
    return {
        "schema": schema_document["schema"],
        "text": build_schema_text_for_ai(schema_document),
    }


def validate_select_sql(raw_sql: str) -> str:
    sql = (raw_sql or "").strip()
    if not sql:
        raise ValueError("Vui lòng nhập câu lệnh SELECT.")
    if "/*" in sql or "*/" in sql or "--" in sql or "#" in sql:
        raise ValueError("Không hỗ trợ comment trong Database Explorer.")

    sql = sub(r";+\s*$", "", sql).strip()
    if ";" in sql:
        raise ValueError("Chỉ được chạy một câu SELECT mỗi lần.")
    if not search(r"^\s*select\b", sql, IGNORECASE):
        raise ValueError("Database Explorer chỉ cho phép câu lệnh SELECT.")

    for token in FORBIDDEN_SQL_TOKENS:
        if search(rf"\b{token}\b", sql, IGNORECASE):
            raise ValueError(f"Không cho phép từ khóa `{token.upper()}` trong Database Explorer.")
    return sql


def _serialize_cell(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, bytes):
        return value.hex()
    return value


def execute_select_query(db: Session, raw_sql: str, max_rows: int = 500) -> dict[str, Any]:
    sql = validate_select_sql(raw_sql)
    row_limit = min(max(max_rows, 1), 2000)
    result = db.execute(text(sql))
    columns = list(result.keys())
    rows = result.fetchmany(row_limit + 1)
    truncated = len(rows) > row_limit
    visible_rows = rows[:row_limit]
    return {
        "columns": columns,
        "rows": [
            {column: _serialize_cell(row[index]) for index, column in enumerate(columns)}
            for row in visible_rows
        ],
        "row_count": len(visible_rows),
        "truncated": truncated,
        "max_rows": row_limit,
    }
