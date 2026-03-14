"""
auth/repository.py
===================
Database access layer for authentication.

BUG FIX (create_employee_and_user):
  The original code called conn.execute("BEGIN") explicitly. Python's sqlite3
  module automatically issues an implicit BEGIN before the first DML statement
  when isolation_level is not None (the default). This caused:
    OperationalError: cannot start a transaction within a transaction
  because SQLite received two BEGIN statements.

  Fix: replaced manual BEGIN/commit/rollback with the 'with conn:' context
  manager, which correctly calls conn.commit() on success and conn.rollback()
  on any exception — no explicit BEGIN needed.
"""

from __future__ import annotations
from database.db import get_db_connection


def find_user_by_email(email: str) -> dict | None:
    conn = get_db_connection()
    row = conn.execute(
        "SELECT * FROM users WHERE email = ?",
        (email.strip().lower(),),
    ).fetchone()
    return dict(row) if row is not None else None


def find_user_by_id(user_id: int) -> dict | None:
    conn = get_db_connection()
    row = conn.execute(
        "SELECT * FROM users WHERE id = ?",
        (int(user_id),),
    ).fetchone()
    return dict(row) if row is not None else None


def email_exists(email: str) -> bool:
    conn = get_db_connection()
    row = conn.execute(
        "SELECT email FROM users WHERE email = ?",
        (email.strip().lower(),),
    ).fetchone()
    return row is not None


def employee_id_exists(employee_id: str) -> bool:
    conn = get_db_connection()
    row = conn.execute(
        "SELECT id FROM employees WHERE id = ?",
        (employee_id,),
    ).fetchone()
    return row is not None


def manager_id_exists(manager_id: str) -> bool:
    """Check whether a manager_id is already registered in the users table."""
    conn = get_db_connection()
    row = conn.execute(
        "SELECT manager_id FROM users WHERE manager_id = ?",
        (manager_id,),
    ).fetchone()
    return row is not None


def get_all_departments() -> list[dict]:
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT id, name FROM departments ORDER BY name"
    ).fetchall()
    return [dict(r) for r in rows]


def insert_user(user_data: dict) -> int:
    conn = get_db_connection()
    cursor = conn.execute(
        """
        INSERT INTO users (name, email, password_hash, role, employee_id, manager_id)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            user_data["name"],
            user_data["email"].strip().lower(),
            user_data["password_hash"],
            user_data["role"],
            user_data.get("employee_id"),   # NULL for managers
            user_data.get("manager_id"),    # NULL for employees
        ),
    )
    conn.commit()
    return cursor.lastrowid


def create_employee_and_user(employee_data: dict, user_data: dict) -> int:
    """
    Atomically insert one employees row and one users row.

    Uses 'with conn:' so both inserts are wrapped in a single transaction:
      - On success  → conn.__exit__ calls conn.commit()
      - On any error → conn.__exit__ calls conn.rollback() and re-raises
    """
    conn = get_db_connection()
    with conn:
        conn.execute(
            "INSERT INTO employees (id, name, email, department_id) VALUES (?, ?, ?, ?)",
            (
                employee_data["id"],
                employee_data["name"],
                employee_data["email"].strip().lower(),
                employee_data.get("department_id"),
            ),
        )
        cursor = conn.execute(
            """
            INSERT INTO users (name, email, password_hash, role, employee_id, manager_id)
            VALUES (?, ?, ?, ?, ?, NULL)
            """,
            (
                user_data["name"],
                user_data["email"].strip().lower(),
                user_data["password_hash"],
                "employee",
                employee_data["id"],
            ),
        )
    return cursor.lastrowid


def update_user_password(email: str, new_hash: str) -> None:
    conn = get_db_connection()
    conn.execute(
        "UPDATE users SET password_hash = ? WHERE email = ?",
        (new_hash, email.strip().lower()),
    )
    conn.commit()
