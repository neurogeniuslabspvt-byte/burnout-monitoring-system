from __future__ import annotations

import logging
import requests
from flask import current_app

logger = logging.getLogger(__name__)

_VALID_LABELS: frozenset[str] = frozenset({"Low", "Medium", "High"})



def predict_burnout(
    data: dict[str, int],
) -> tuple[float | None, str]:

    payload    = _build_payload(data)
    ml_url     = current_app.config.get("ML_API_URL",     "https://burnout-api-rj45.onrender.com/predict")
    ml_timeout = current_app.config.get("ML_API_TIMEOUT", 30)

    try:
        response = requests.post(ml_url, json=payload, timeout=ml_timeout)
        response.raise_for_status()

    except requests.exceptions.Timeout:
        logger.warning("ML API timed out after %ss (url=%s)", ml_timeout, ml_url)
        return _handle_api_error()

    except requests.exceptions.ConnectionError:
        logger.warning("ML API connection failed (url=%s)", ml_url)
        return _handle_api_error()

    except requests.exceptions.HTTPError as exc:
        logger.warning(
            "ML API returned HTTP %s (url=%s): %s",
            exc.response.status_code, ml_url, exc,
        )
        return _handle_api_error()

    except requests.exceptions.RequestException as exc:
        logger.warning("ML API request failed (url=%s): %s", ml_url, exc)
        return _handle_api_error()

    try:
        body = response.json()
    except ValueError:
        logger.warning("ML API returned non-JSON body (url=%s): %r", ml_url, response.text[:200])
        return _handle_api_error()

    score, label = _validate_api_response(body)
    if score is None:
        return _handle_api_error()

    return score, label



def _build_payload(data: dict[str, int]) -> dict[str, int]:
    """Extract the four survey fields the ML API expects."""
    return {
        "happiness":  int(data["happiness"]),
        "motivation": int(data["motivation"]),
        "stress":     int(data["stress"]),
        "caffeine":   int(data["caffeine"]),
    }


def _validate_api_response(
    body: dict,
) -> tuple[float | None, str | None]:
    if "burnout_score" not in body:
        logger.warning("ML API response missing 'burnout_score'. Body: %r", body)
        return None, None

    if "predicted_label" not in body:
        logger.warning("ML API response missing 'predicted_label'. Body: %r", body)
        return None, None

    score = body["burnout_score"]
    label = body["predicted_label"]

    if not isinstance(score, (int, float)):
        logger.warning(
            "ML API 'burnout_score' not numeric: %r (type=%s)",
            score, type(score).__name__,
        )
        return None, None

    if not (0.0 <= float(score) <= 100.0):
        logger.warning("ML API 'burnout_score' out of range: %r", score)
        return None, None

    if label not in _VALID_LABELS:
        logger.warning(
            "ML API 'predicted_label' not a valid category %r: %r",
            sorted(_VALID_LABELS), label,
        )
        return None, None

    return round(float(score), 1), str(label)


def _handle_api_error() -> tuple[None, str]:
    return None, "Unavailable"
