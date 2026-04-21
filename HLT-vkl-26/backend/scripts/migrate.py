from __future__ import annotations

import argparse
import sys

from database.migrations import (
    MigrationError,
    apply_migrations,
    current_version,
    pending_migrations,
)


def cmd_upgrade() -> int:
    applied = apply_migrations()
    if applied:
        for migration in applied:
            print(f"Applied {migration.version}: {migration.name}")
    else:
        print("Schema already up to date.")
    return 0


def cmd_status() -> int:
    current = current_version()
    pending = pending_migrations()
    print(f"Current version: {current or 'none'}")
    if pending:
        print("Pending migrations:")
        for migration in pending:
            print(f" - {migration.version}: {migration.name}")
    else:
        print("Pending migrations: none")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Apply local SQL migrations for the backend database.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("upgrade", help="Apply all pending migrations.")
    subparsers.add_parser("status", help="Show current and pending migration versions.")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        if args.command == "upgrade":
            return cmd_upgrade()
        if args.command == "status":
            return cmd_status()
    except MigrationError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
