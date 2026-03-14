from __future__ import annotations

from datetime import date, timedelta

from utils.date_utils  import get_last_week_dates
from utils.chart_utils import generate_week_labels, normalize_scores


def get_week_history(
    employee_id: str,
) -> tuple[list[float | None], list[str], float | None]:

    raw_records = _fetch_records(employee_id)
    filled      = fill_missing_days(raw_records)
    raw_scores  = _extract_scores(filled)
    scores      = normalize_scores(raw_scores)
    labels      = generate_week_labels()
    avg_score   = calculate_week_average(scores)
    return scores, labels, avg_score



def _fetch_records(employee_id: str) -> list[dict]:

    from employee.repository import get_week_responses

    rows = get_week_responses(employee_id)
    return [
        {"date": str(row["date"]), "burnout_score": row["burnout_score"]}
        for row in rows
    ]


def fill_missing_days(records: list[dict]) -> list[dict]:
    score_by_date: dict[str, float | None] = {
        r["date"]: r["burnout_score"] for r in records
    }

    start_iso, end_iso = get_last_week_dates()
    start   = date.fromisoformat(start_iso)
    end     = date.fromisoformat(end_iso)
    filled: list[dict] = []
    current = start

    while current <= end:
        iso = current.isoformat()
        filled.append({
            "date":          iso,
            "burnout_score": score_by_date.get(iso),
        })
        current += timedelta(days=1)

    return filled



def _extract_scores(records: list[dict]) -> list[float | None]:
    """Pull the burnout_score value out of each filled record."""
    return [r["burnout_score"] for r in records]


def calculate_week_average(scores: list[float | None]) -> float | None:
    valid = [s for s in scores if s is not None]
    if not valid:
        return None
    return round(sum(valid) / len(valid), 1)
