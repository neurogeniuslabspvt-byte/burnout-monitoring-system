from __future__ import annotations

import os
import sqlite3

from flask import current_app, g

_MEMORY_DB: str = ":memory:"


def get_db_connection() -> sqlite3.Connection:
    if "db" not in g:
        db_path = current_app.config["DATABASE_URI"]

        if db_path != _MEMORY_DB:
            os.makedirs(os.path.dirname(db_path), exist_ok=True)

        g.db = sqlite3.connect(
            db_path,
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
        g.db.execute("PRAGMA journal_mode = WAL")

    return g.db


def close_db_connection(e=None) -> None:
    db: sqlite3.Connection | None = g.pop("db", None)
    if db is not None:
        db.close()


def init_db() -> None:
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")

    if not os.path.exists(schema_path):
        raise FileNotFoundError(
            f"[init_db] Schema file not found at '{schema_path}'."
        )

    conn = get_db_connection()
    with open(schema_path, "r", encoding="utf-8") as f:
        sql = f.read()

    conn.executescript(sql)
    conn.commit()
    _run_migrations(conn)


def _run_migrations(conn: sqlite3.Connection) -> None:
    existing_columns = {
        row[1]  # column name is index 1 in PRAGMA table_info rows
        for row in conn.execute("PRAGMA table_info(users)")
    }

    if "manager_id" not in existing_columns:
        # SQLite does not allow ADD COLUMN with a UNIQUE constraint directly.
        # Solution: add the column without UNIQUE, then create a unique index.
        conn.execute("ALTER TABLE users ADD COLUMN manager_id TEXT")
        conn.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_users_manager_id "
            "ON users (manager_id) WHERE manager_id IS NOT NULL"
        )
        conn.commit()
