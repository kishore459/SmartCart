"""One-time migration of SmartCart data from MySQL to SQLite.

Usage:
    python database/migrate_mysql_to_sqlite.py \
      --host localhost --user root --database smartcart_db

The password is read securely if --password is omitted. This script preserves
primary keys so the relationships between users, products, orders, and order
items remain valid.
"""

import argparse
import datetime
import decimal
import getpass
import os
import sqlite3
import sys
from pathlib import Path

try:
    import mysql.connector
except ImportError as exc:
    raise SystemExit(
        "Install the one-time migration dependency first: "
        "pip install -r database/requirements-migration.txt"
    ) from exc


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SQLITE_PATH = PROJECT_ROOT / "database" / "smartcart.db"
SCHEMA_PATH = PROJECT_ROOT / "database" / "schema_sqlite.sql"
TABLES = ("admin", "users", "products", "orders", "order_items")


def sqlite_value(value):
    """Convert values returned by MySQL Connector into SQLite-safe values."""
    if isinstance(value, decimal.Decimal):
        return str(value)
    if isinstance(value, (datetime.datetime, datetime.date, datetime.time)):
        return value.isoformat(sep=" ") if isinstance(value, datetime.datetime) else value.isoformat()
    return value


def table_count(connection, table):
    return connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


def prepare_sqlite_database(sqlite_path, replace):
    sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(sqlite_path)
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))

    existing = {table: table_count(connection, table) for table in TABLES}
    if any(existing.values()) and not replace:
        connection.close()
        details = ", ".join(f"{table}={count}" for table, count in existing.items() if count)
        raise RuntimeError(
            f"SQLite destination already contains data ({details}). "
            "Use --replace only after backing it up."
        )
    if replace:
        # Delete children first, then parents, while retaining the schema.
        for table in reversed(TABLES):
            connection.execute(f"DELETE FROM {table}")
        connection.commit()
    return connection


def migrate(mysql_connection, sqlite_connection):
    mysql_cursor = mysql_connection.cursor(dictionary=True)
    try:
        sqlite_connection.execute("PRAGMA foreign_keys = OFF")
        for table in TABLES:
            mysql_cursor.execute(f"SELECT * FROM {table}")
            rows = mysql_cursor.fetchall()
            if not rows:
                print(f"{table}: 0 rows")
                continue

            columns = list(rows[0])
            placeholders = ", ".join("?" for _ in columns)
            statement = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"
            values = [tuple(sqlite_value(row[column]) for column in columns) for row in rows]
            sqlite_connection.executemany(statement, values)
            print(f"{table}: {len(rows)} rows copied")

        sqlite_connection.commit()
        sqlite_connection.execute("PRAGMA foreign_keys = ON")
        violations = sqlite_connection.execute("PRAGMA foreign_key_check").fetchall()
        if violations:
            raise RuntimeError(f"Foreign-key validation failed: {violations}")
    except Exception:
        sqlite_connection.rollback()
        raise
    finally:
        mysql_cursor.close()


def main():
    parser = argparse.ArgumentParser(description="Copy SmartCart data from MySQL to SQLite.")
    parser.add_argument("--host", default="localhost", help="MySQL host (default: localhost)")
    parser.add_argument("--port", type=int, default=3306, help="MySQL port (default: 3306)")
    parser.add_argument("--user", required=True, help="MySQL username")
    parser.add_argument("--password", help="MySQL password; omit to enter it securely")
    parser.add_argument("--database", required=True, help="Source MySQL database name")
    parser.add_argument("--sqlite-path", type=Path, default=DEFAULT_SQLITE_PATH,
                        help=f"Destination SQLite file (default: {DEFAULT_SQLITE_PATH})")
    parser.add_argument("--replace", action="store_true",
                        help="Replace existing SQLite rows after making a backup")
    args = parser.parse_args()

    password = args.password or os.environ.get("SMARTCART_MYSQL_PASSWORD")
    if password is None:
        password = getpass.getpass("MySQL password: ")
    mysql_connection = mysql.connector.connect(
        host=args.host, port=args.port, user=args.user, password=password, database=args.database
    )
    sqlite_connection = None
    try:
        sqlite_connection = prepare_sqlite_database(args.sqlite_path.resolve(), args.replace)
        migrate(mysql_connection, sqlite_connection)
        print(f"Migration complete: {args.sqlite_path.resolve()}")
    finally:
        if sqlite_connection is not None:
            sqlite_connection.close()
        mysql_connection.close()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Migration failed: {exc}", file=sys.stderr)
        sys.exit(1)
