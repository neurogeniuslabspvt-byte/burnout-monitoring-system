from __future__ import annotations

from database.db import get_db_connection
from utils.date_utils import get_today_date, get_last_week_dates


def save_survey_response(
    employee_id: str,
    happiness: int,
    motivation: int,
    stress: int,
    caffeine: int,
    burnout_score: float | None,
    burnout_label: str | None,
) -> None:
    today = get_today_date()
    conn  = get_db_connection()
    conn.execute(
        """
        INSERT INTO survey_responses
            (employee_id, date, happiness, motivation, stress,
             caffeine, burnout_score, burnout_label)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (employee_id, today, happiness, motivation, stress,
         caffeine, burnout_score, burnout_label),
    )
    conn.commit()


def get_today_response(employee_id: str):
    today = get_today_date()
    conn  = get_db_connection()
    return conn.execute(
        "SELECT * FROM survey_responses WHERE employee_id = ? AND date = ?",
        (employee_id, today),
    ).fetchone()


def get_week_responses(employee_id: str) -> list:
    start_date, end_date = get_last_week_dates()
    conn = get_db_connection()
    return conn.execute(
        """
        SELECT date, burnout_score
          FROM survey_responses
         WHERE employee_id = ?
           AND date BETWEEN ? AND ?
         ORDER BY date ASC
        """,
        (employee_id, start_date, end_date),
    ).fetchall()
