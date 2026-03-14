from __future__ import annotations

from functools import wraps

from flask import session, redirect, url_for, abort


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth.login_page"))
        return f(*args, **kwargs)

    return decorated



def employee_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth.login_page"))

        if session.get("role") != "employee":
            abort(403)

        return f(*args, **kwargs)

    return decorated



def manager_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth.login_page"))

        if session.get("role") != "manager":
            abort(403)

        return f(*args, **kwargs)

    return decorated
