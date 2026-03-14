from __future__ import annotations
from database.db      import get_db_connection
from utils.date_utils import get_last_week_dates, get_today_date


def fetch_all_employees_latest_response() -> list[dict]:
    conn = get_db_connection()
    rows = conn.execute(
        """
        SELECT
            e.id            AS employee_id,
            e.name          AS name,
            e.email         AS email,
            d.name          AS department,
            sr.burnout_score AS burnout_score,
            sr.burnout_label AS burnout_label,
            sr.date          AS last_seen
        FROM employees e
        LEFT JOIN departments d ON d.id = e.department_id
        LEFT JOIN survey_responses sr
               ON sr.employee_id = e.id
              AND sr.date = (
                      SELECT MAX(sr2.date)
                        FROM survey_responses sr2
                       WHERE sr2.employee_id = e.id
                  )
        ORDER BY e.name ASC
        """
    ).fetchall()
    return [dict(row) for row in rows]


def fetch_employee_info(employee_id: str) -> dict | None:
    conn = get_db_connection()
    row = conn.execute(
        """
        SELECT e.id AS id, e.name AS name, e.email AS email, d.name AS department
        FROM employees e
        LEFT JOIN departments d ON d.id = e.department_id
        WHERE e.id = ?
        """,
        (employee_id,),
    ).fetchone()
    return dict(row) if row is not None else None


def fetch_employee_trend(employee_id: str) -> list[dict]:
    start_date, end_date = get_last_week_dates()
    conn = get_db_connection()
    rows = conn.execute(
        """
        SELECT date, happiness, motivation, stress, caffeine,
               burnout_score, burnout_label
        FROM survey_responses
        WHERE employee_id = ?
          AND date BETWEEN ? AND ?
        ORDER BY date ASC
        """,
        (employee_id, start_date, end_date),
    ).fetchall()
    return [dict(row) for row in rows]


def fetch_weekly_team_trend() -> list[dict]:
    start_date, end_date = get_last_week_dates()
    conn = get_db_connection()
    rows = conn.execute(
        """
        SELECT date, ROUND(AVG(burnout_score), 1) AS avg_score
        FROM survey_responses
        WHERE date BETWEEN ? AND ?
          AND burnout_score IS NOT NULL
        GROUP BY date
        HAVING COUNT(burnout_score) > 0
        ORDER BY date ASC
        """,
        (start_date, end_date),
    ).fetchall()
    return [dict(row) for row in rows]
