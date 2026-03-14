from __future__ import annotations

from datetime import date, timedelta


def get_today_date() -> str:
    return date.today().isoformat()


def get_last_week_dates() -> tuple[str, str]:
    today = date.today()
    start = today - timedelta(days=6)   # FIX: was days=7 (8-day window)
    return start.isoformat(), today.isoformat()
