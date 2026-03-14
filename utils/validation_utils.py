from __future__ import annotations

_FIELD_RULES: dict[str, dict] = {
    "happiness": {
        "label": "Happiness",
        "min":   1,
        "max":   10,
    },
    "motivation": {
        "label": "Motivation",
        "min":   1,
        "max":   10,
    },
    "stress": {
        "label": "Stress",
        "min":   1,
        "max":   10,
    },
    "caffeine": {
        "label": "Caffeine cups",
        "min":   0,
        "max":   6,
    },
}


def validate_survey_inputs(raw: dict[str, str | None]) -> bool | str:

    for field, rules in _FIELD_RULES.items():
        label   = rules["label"]
        min_val = rules["min"]
        max_val = rules["max"]
        raw_val = raw.get(field)

        # ── 1. Presence ────────────────────────────────────────────────────
        if raw_val is None or str(raw_val).strip() == "":
            return f"{label} is required."

        # ── 2. Type ────────────────────────────────────────────────────────
        try:
            numeric_val = int(str(raw_val).strip())
        except (ValueError, TypeError):
            return f"{label} must be a whole number."

        # ── 3. Range ───────────────────────────────────────────────────────
        if not (min_val <= numeric_val <= max_val):
            return (
                f"{label} must be between {min_val} and {max_val}. "
                f"You entered: {numeric_val}."
            )

    return True


def sanitize_inputs(
    raw: dict[str, str | None],
) -> tuple[int, int, int, int]:
    return (
        int(str(raw["happiness"]).strip()),
        int(str(raw["motivation"]).strip()),
        int(str(raw["stress"]).strip()),
        int(str(raw["caffeine"]).strip()),
    )



def validate_employee_id(employee_id: str | None) -> bool | str:

    if not employee_id or not str(employee_id).strip():
        return "Employee ID is missing. Please log in again."

    from database.db import get_db_connection

    conn = get_db_connection()
    row  = conn.execute(
        "SELECT id FROM employees WHERE id = ?",
        (str(employee_id).strip(),),
    ).fetchone()

    if row is None:
        return (
            f"Employee '{employee_id}' was not found. "
            "Your account may have been removed. Please contact your administrator."
        )

    return True
