from .repository import get_today_response


def check_today_submission(employee_id: str) -> bool:
    return get_today_response(employee_id) is not None
