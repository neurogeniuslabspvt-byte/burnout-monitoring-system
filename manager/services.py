from __future__ import annotations

from utils.chart_utils import normalize_scores, generate_week_labels
from utils.date_utils  import get_last_week_dates

from manager.repository import (
    fetch_all_employees_latest_response,
    fetch_employee_info,
    fetch_employee_trend,
    fetch_weekly_team_trend,
)

_LOW_MAX:    float = 35.0
_MEDIUM_MAX: float = 65.0


def _score_level(score: float | None) -> str:
    if score is None:
        return "no_data"
    if score <= _LOW_MAX:
        return "low"
    if score <= _MEDIUM_MAX:
        return "medium"
    return "high"


def get_burnout_distribution() -> dict:
    rows = fetch_all_employees_latest_response()
    counts: dict[str, int] = {"low": 0, "medium": 0, "high": 0, "no_data": 0}
    for row in rows:
        level = _score_level(row["burnout_score"])
        counts[level] += 1

    total     = len(rows)
    submitted = counts["low"] + counts["medium"] + counts["high"]

    def _pct(n: int) -> float:
        return round(n / total * 100, 1) if total else 0.0

    return {
        "total":      total,
        "submitted":  submitted,
        "low":        counts["low"],
        "medium":     counts["medium"],
        "high":       counts["high"],
        "no_data":    counts["no_data"],
        "low_pct":    _pct(counts["low"]),
        "medium_pct": _pct(counts["medium"]),
        "high_pct":   _pct(counts["high"]),
    }


def get_employee_burnout_list() -> list[dict]:
    rows       = fetch_all_employees_latest_response()
    raw_scores = [row["burnout_score"] for row in rows]
    normed     = normalize_scores(raw_scores)

    employees: list[dict] = []
    for row, score in zip(rows, normed):
        employees.append({
            "employee_id":   row["employee_id"],
            "name":          row["name"],
            "email":         row["email"],
            "department":    row["department"],
            "burnout_score": score,
            "burnout_label": row["burnout_label"],
            "level":         _score_level(score),
            "last_seen":     row["last_seen"],
        })

    _SORT_ORDER = {"high": 0, "medium": 1, "low": 2, "no_data": 3}
    employees.sort(key=lambda e: _SORT_ORDER[e["level"]])
    return employees


def get_employee_burnout_trend(employee_id: str) -> dict:
    emp = fetch_employee_info(employee_id)
    if emp is None:
        return {
            "employee":       {"id": employee_id, "name": "", "email": "", "department": None},
            "scores":         [],
            "labels":         [],
            "avg_score":      None,
            "latest_score":   None,
            "latest_label":   None,
            "latest_level":   "no_data",
            "has_data":       False,
            "survey_history": [],
        }

    trend_rows = fetch_employee_trend(employee_id)
    filled     = _fill_trend_gaps(trend_rows)
    raw_scores = [r["burnout_score"] for r in filled]
    scores     = normalize_scores(raw_scores)
    labels     = generate_week_labels()
    avg_score  = _week_average(scores)

    latest_score: float | None = None
    latest_label: str  | None  = None
    for r, s in zip(reversed(filled), reversed(scores)):
        if s is not None:
            latest_score = s
            latest_label = r.get("burnout_label")
            break

    survey_history: list[dict] = []
    for r, s in zip(filled, scores):
        # Include any row where the employee actually submitted survey inputs,
        # even if the ML API was unavailable and burnout_score is None.
        if r.get("happiness") is not None:
            survey_history.append({
                "date":          r["date"],
                "happiness":     r.get("happiness"),
                "motivation":    r.get("motivation"),
                "stress":        r.get("stress"),
                "caffeine":      r.get("caffeine"),
                "burnout_score": s,
                "burnout_label": r.get("burnout_label"),
                "level":         _score_level(s),
            })
    survey_history.reverse()

    return {
        "employee": {
            "id":         emp["id"],
            "name":       emp["name"],
            "email":      emp["email"],
            "department": emp["department"],
        },
        "scores":         scores,
        "labels":         labels,
        "avg_score":      avg_score,
        "latest_score":   latest_score,
        "latest_label":   latest_label,
        "latest_level":   _score_level(latest_score),
        "has_data":       any(s is not None for s in scores),
        "survey_history": survey_history,
    }


def get_dashboard_summary() -> dict:
    distribution = get_burnout_distribution()

    rows       = fetch_all_employees_latest_response()
    all_scores = [r["burnout_score"] for r in rows if r["burnout_score"] is not None]
    avg_score  = round(sum(all_scores) / len(all_scores), 1) if all_scores else None

    trend_rows   = fetch_weekly_team_trend()
    filled_trend = _fill_team_trend_gaps(trend_rows)
    trend_scores = [r["avg_score"] for r in filled_trend]
    trend_labels = generate_week_labels()

    raw_scores = [r["burnout_score"] for r in rows]
    normed     = normalize_scores(raw_scores)

    high_risk: list[dict] = []
    for row, score in zip(rows, normed):
        if score is not None and score > _MEDIUM_MAX:
            high_risk.append({
                "employee_id":   row["employee_id"],
                "name":          row["name"],
                "department":    row["department"],
                "burnout_score": score,
                "level":         "high",
                "last_seen":     row["last_seen"],
            })

    high_risk.sort(key=lambda e: e["burnout_score"], reverse=True)

    return {
        "distribution": distribution,
        "avg_score":    avg_score,
        "trend_labels": trend_labels,
        "trend_scores": trend_scores,
        "high_risk":    high_risk,
    }


def _fill_trend_gaps(rows: list[dict]) -> list[dict]:
    from datetime import date, timedelta
    # str(r["date"]) normalises both datetime.date objects (returned by sqlite3
    # when detect_types=PARSE_DECLTYPES is set) and plain strings to "YYYY-MM-DD"
    # so the dict lookup always matches current.isoformat().
    by_date = {str(r["date"]): r for r in rows}
    start_iso, end_iso = get_last_week_dates()
    start = date.fromisoformat(start_iso)
    end   = date.fromisoformat(end_iso)
    filled: list[dict] = []
    current = start
    while current <= end:
        iso = current.isoformat()
        filled.append(by_date.get(iso, {
            "date": iso, "burnout_score": None, "burnout_label": None,
            "happiness": None, "motivation": None, "stress": None, "caffeine": None,
        }))
        current += timedelta(days=1)
    return filled


def _fill_team_trend_gaps(rows: list[dict]) -> list[dict]:
    from datetime import date, timedelta
    by_date = {str(r["date"]): r for r in rows}
    start_iso, end_iso = get_last_week_dates()
    start = date.fromisoformat(start_iso)
    end   = date.fromisoformat(end_iso)
    filled: list[dict] = []
    current = start
    while current <= end:
        iso = current.isoformat()
        filled.append(by_date.get(iso, {"date": iso, "avg_score": None}))
        current += timedelta(days=1)
    return filled


def _week_average(scores: list[float | None]) -> float | None:
    valid = [s for s in scores if s is not None]
    if not valid:
        return None
    return round(sum(valid) / len(valid), 1)