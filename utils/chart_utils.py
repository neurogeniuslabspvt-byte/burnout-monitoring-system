from __future__ import annotations

from datetime import date, timedelta   

from utils.date_utils import get_last_week_dates



_LOW_MAX:    float = 35.0
_MEDIUM_MAX: float = 65.0

_SCORE_MIN: float = 0.0
_SCORE_MAX: float = 100.0

# Index 0 = Monday (Python's date.weekday())
_DAY_ABBR: tuple[str, ...] = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")

_COLORS: dict[str, dict[str, str]] = {
    "low": {
        "background": "rgba(129,178,154,0.85)",
        "border":     "#4d9e7a",
    },
    "medium": {
        "background": "rgba(242,204,143,0.90)",
        "border":     "#c9920a",
    },
    "high": {
        "background": "rgba(224,122,95,0.90)",
        "border":     "#d4614a",
    },
    "none": {
        "background": "rgba(200,190,180,0.30)",
        "border":     "#c0b4a4",
    },
}

_AVG_LINE_COLOR: str = "#6b8cba"




def generate_week_labels() -> list[str]:

    start_iso, end_iso = get_last_week_dates()
    start = date.fromisoformat(start_iso)
    end   = date.fromisoformat(end_iso)

    labels: list[str] = []
    current = start
    while current <= end:
        labels.append(_format_day_label(current))
        current += timedelta(days=1)  

    return labels




def normalize_scores(
    scores: list[float | None],
) -> list[float | None]:

    result: list[float | None] = []
    for s in scores:
        if s is None:
            result.append(None)
        else:
            clamped = max(_SCORE_MIN, min(_SCORE_MAX, float(s)))
            result.append(round(clamped, 1))
    return result


def build_chart_dataset(
    scores: list[float | None],
    labels: list[str],
    avg_score: float | None,
) -> dict:

    background_colors = [_get_bar_color(s)  for s in scores]
    border_colors     = [_get_bar_border(s) for s in scores]

    bar_dataset: dict = {
        "type":            "bar",
        "label":           "Burnout Score",
        "data":            scores,
        "backgroundColor": background_colors,
        "borderColor":     border_colors,
        "borderWidth":     2,
        "borderRadius":    10,
        "borderSkipped":   False,
    }

    datasets: list[dict] = [bar_dataset]

    if avg_score is not None:
        avg_dataset: dict = {
            "type":        "line",
            "label":       f"Average ({avg_score})",
            "data":        [avg_score] * len(scores),
            "borderColor": _AVG_LINE_COLOR,
            "borderWidth": 2,
            "borderDash":  [6, 4],
            "pointRadius": 0,
            "fill":        False,
            "tension":     0,
        }
        datasets.append(avg_dataset)

    return {
        "labels":   labels,
        "datasets": datasets,
    }


def _score_level(score: float | None) -> str:
    """Map a numeric score to its burnout level string."""
    if score is None:
        return "none"
    if score <= _LOW_MAX:
        return "low"
    if score <= _MEDIUM_MAX:
        return "medium"
    return "high"


def _get_bar_color(score: float | None) -> str:
    """Return the Chart.js ``backgroundColor`` for a given score."""
    return _COLORS[_score_level(score)]["background"]


def _get_bar_border(score: float | None) -> str:
    """Return the Chart.js ``borderColor`` for a given score."""
    return _COLORS[_score_level(score)]["border"]


def _format_day_label(d: date) -> str:
    """Format a single date as a compact chart label, e.g. ``"Mon 03"``."""
    return f"{_DAY_ABBR[d.weekday()]} {d.day:02d}"
