from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, URL

from app.core.config import get_settings


ROOT_DIR = Path(__file__).resolve().parents[1]
MIGRATIONS_DIR = ROOT_DIR / "migrations" / "versions"
VERSION_TABLE = "schema_migrations"
BASELINE_SCHEMA_VERSION = "001"
BASELINE_SEED_VERSION = "002"
BASELINE_TABLES = {
    "agent",
    "agent_capability",
    "agent_update_package",
    "agent_update_history",
    "task",
    "operation",
    "operation_task",
    "operation_execution",
    "target",
    "target_attribute_definition",
    "target_attribute_value",
    "target_group",
    "target_group_mapping",
    "vulnerability",
    "vulnerability_reference",
    "vulnerability_script",
    "task_execution",
    "scan_result",
    "scan_result_finding",
    "finding_asset",
    "operation_result_import_export",
    "report_template",
    "generated_report",
    "report_snapshot",
}


@dataclass(frozen=True)
class MigrationFile:
    version: str
    name: str
    path: Path


class MigrationError(RuntimeError):
    """Raised when schema migration state is invalid."""


def _build_mysql_url(database: str | None) -> URL:
    settings = get_settings()
    return URL.create(
        "mysql+pymysql",
        username=settings.mysql_user,
        password=settings.mysql_password,
        host=settings.mysql_host,
        port=settings.mysql_port,
        database=database,
        query={"charset": "utf8mb4"},
    )


def _admin_engine() -> Engine:
    return create_engine(_build_mysql_url(None), future=True, pool_pre_ping=True)


def _database_engine() -> Engine:
    settings = get_settings()
    return create_engine(_build_mysql_url(settings.mysql_database), future=True, pool_pre_ping=True)


def _load_migration_files() -> list[MigrationFile]:
    files: list[MigrationFile] = []
    for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
        stem = path.stem
        if "__" not in stem:
            raise MigrationError(f"Migration file must follow <version>__<name>.sql: {path.name}")
        version, name = stem.split("__", 1)
        files.append(MigrationFile(version=version, name=name.replace("_", " "), path=path))
    return files


def _split_sql_statements(sql_text: str) -> list[str]:
    statements: list[str] = []
    buffer: list[str] = []
    in_single = False
    in_double = False
    escape = False
    line_comment = False
    block_comment = False
    skip_next = False

    for index, char in enumerate(sql_text):
        if skip_next:
            skip_next = False
            continue

        next_char = sql_text[index + 1] if index + 1 < len(sql_text) else ""

        if line_comment:
            if char == "\n":
                line_comment = False
            continue

        if block_comment:
            if char == "*" and next_char == "/":
                block_comment = False
                skip_next = True
            continue

        if not in_single and not in_double:
            if char == "-" and next_char == "-":
                line_comment = True
                skip_next = True
                continue
            if char == "/" and next_char == "*":
                block_comment = True
                skip_next = True
                continue

        buffer.append(char)

        if escape:
            escape = False
            continue

        if char == "\\":
            escape = True
            continue

        if char == "'" and not in_double:
            in_single = not in_single
            continue

        if char == '"' and not in_single:
            in_double = not in_double
            continue

        if char == ";" and not in_single and not in_double:
            statement = "".join(buffer).strip()
            if statement:
                statements.append(statement[:-1].strip())
            buffer.clear()

    trailing = "".join(buffer).strip()
    if trailing:
        statements.append(trailing)
    return [statement for statement in statements if statement]


def _ensure_database_exists() -> None:
    settings = get_settings()
    database_name = settings.mysql_database.replace("`", "``")
    with _admin_engine().begin() as connection:
        connection.execute(
            text(
                f"CREATE DATABASE IF NOT EXISTS `{database_name}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        )


def _ensure_version_table(engine: Engine) -> None:
    with engine.begin() as connection:
        connection.execute(
            text(
                f"""
                CREATE TABLE IF NOT EXISTS {VERSION_TABLE} (
                    version VARCHAR(255) PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    applied_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        )


def _applied_versions(engine: Engine) -> set[str]:
    with engine.connect() as connection:
        rows = connection.execute(text(f"SELECT version FROM {VERSION_TABLE} ORDER BY version")).scalars().all()
    return set(rows)


def _insert_version(engine: Engine, version: str, name: str) -> None:
    with engine.begin() as connection:
        connection.execute(
            text(
                f"""
                INSERT INTO {VERSION_TABLE} (version, name)
                VALUES (:version, :name)
                ON DUPLICATE KEY UPDATE name = VALUES(name)
                """
            ),
            {"version": version, "name": name},
        )


def _existing_tables(engine: Engine) -> set[str]:
    settings = get_settings()
    with engine.connect() as connection:
        rows = connection.execute(
            text(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = :schema_name
                """
            ),
            {"schema_name": settings.mysql_database},
        ).scalars().all()
    return set(rows)


def _sample_seed_present(engine: Engine) -> bool:
    required_checks = [
        ("agent", "code", "AG-NMAP-01"),
        ("task", "code", "TASK-NMAP-TCP"),
        ("report_template", "code", "RPT-WEEKLY-SUMMARY"),
    ]
    with engine.connect() as connection:
        for table_name, column_name, expected_value in required_checks:
            found = connection.execute(
                text(f"SELECT 1 FROM {table_name} WHERE {column_name} = :expected_value LIMIT 1"),
                {"expected_value": expected_value},
            ).scalar_one_or_none()
            if found is None:
                return False
    return True


def _stamp_legacy_state(engine: Engine) -> set[str]:
    applied = _applied_versions(engine)
    if applied:
        return applied

    migration_names = {migration.version: migration.name for migration in _load_migration_files()}
    existing_tables = _existing_tables(engine)

    if BASELINE_TABLES.issubset(existing_tables):
        _insert_version(engine, BASELINE_SCHEMA_VERSION, migration_names[BASELINE_SCHEMA_VERSION])
        applied.add(BASELINE_SCHEMA_VERSION)

    if BASELINE_SCHEMA_VERSION in applied and _sample_seed_present(engine):
        _insert_version(engine, BASELINE_SEED_VERSION, migration_names[BASELINE_SEED_VERSION])
        applied.add(BASELINE_SEED_VERSION)

    return applied


def current_version() -> str | None:
    _ensure_database_exists()
    engine = _database_engine()
    _ensure_version_table(engine)
    _stamp_legacy_state(engine)
    with engine.connect() as connection:
        row = connection.execute(
            text(f"SELECT version FROM {VERSION_TABLE} ORDER BY version DESC LIMIT 1")
        ).scalar_one_or_none()
    return row


def pending_migrations() -> list[MigrationFile]:
    _ensure_database_exists()
    engine = _database_engine()
    _ensure_version_table(engine)
    applied = _stamp_legacy_state(engine)
    return [migration for migration in _load_migration_files() if migration.version not in applied]


def apply_migrations() -> list[MigrationFile]:
    _ensure_database_exists()
    engine = _database_engine()
    _ensure_version_table(engine)
    applied = _stamp_legacy_state(engine)
    executed: list[MigrationFile] = []

    for migration in _load_migration_files():
        if migration.version in applied:
            continue
        statements = _split_sql_statements(migration.path.read_text(encoding="utf-8"))
        with engine.begin() as connection:
            for statement in statements:
                connection.exec_driver_sql(statement)
            connection.execute(
                text(f"INSERT INTO {VERSION_TABLE} (version, name) VALUES (:version, :name)"),
                {"version": migration.version, "name": migration.name},
            )
        executed.append(migration)
        applied.add(migration.version)

    return executed


def ensure_schema_up_to_date(*, auto_apply: bool = False) -> None:
    outstanding = pending_migrations()
    if not outstanding:
        return
    if auto_apply:
        apply_migrations()
        return
    names = ", ".join(f"{migration.version} ({migration.name})" for migration in outstanding)
    raise MigrationError(
        "Database schema is behind the checked-in migrations. "
        f"Run `python scripts\\migrate.py upgrade` before starting the app. Pending: {names}"
    )
