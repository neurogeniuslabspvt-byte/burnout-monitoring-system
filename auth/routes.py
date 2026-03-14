from __future__ import annotations

from datetime import datetime

from flask import (
    Blueprint, render_template, redirect, url_for,
    request, session, flash, current_app,
)

from auth.services import (
    authenticate_user,
    create_new_user,
    send_password_reset_otp,
    reset_user_password,
)
from auth.repository import get_all_departments

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


def _redirect_by_role():
    role = session.get("role")
    if role == "manager":
        return redirect(url_for("manager.manager_dashboard"))
    return redirect(url_for("employee.employee_dashboard"))


@auth_bp.route("/login", methods=["GET"])
def login_page():
    if "user_id" in session:
        return _redirect_by_role()
    return render_template("auth/login.html")


@auth_bp.route("/login", methods=["POST"])
def login_user():
    email    = request.form.get("email",    "").strip()
    password = request.form.get("password", "")

    result = authenticate_user(email, password)

    if isinstance(result, str):
        flash(result)
        return render_template("auth/login.html")

    user = result
    session.clear()
    session["user_id"] = user["id"]
    session["role"]    = user["role"]
    session["name"]    = user["name"]

    if user["role"] == "employee":
        session["employee_id"] = user["employee_id"]
    else:
        session["manager_id"] = user["id"]

    return _redirect_by_role()


@auth_bp.route("/signup", methods=["GET"])
def signup_page():
    if "user_id" in session:
        return _redirect_by_role()
    departments = get_all_departments()
    return render_template("auth/signup.html", departments=departments)


@auth_bp.route("/signup", methods=["POST"])
def register_user():
    role = request.form.get("role", "employee").strip().lower()

    data = {
        "role":             role,
        "name":             request.form.get("name",             ""),
        "email":            request.form.get("email",            ""),
        "password":         request.form.get("password",         ""),
        "confirm_password": request.form.get("confirm_password", ""),
        # Employee-only fields
        "employee_id":      request.form.get("employee_id",      ""),
        "department_id":    request.form.get("department_id",    "") or None,
        # Manager-only field
        "manager_id":       request.form.get("manager_id",       ""),
    }

    try:
        result = create_new_user(data)
    except Exception:
        flash(
            "Account could not be created due to a database error. "
            "Please verify your ID is correct.",
            "error",
        )
        departments = get_all_departments()
        return render_template("auth/signup.html", departments=departments)

    if isinstance(result, str):
        flash(result)
        departments = get_all_departments()
        return render_template("auth/signup.html", departments=departments)

    flash("Account created successfully! Please sign in.", "success")
    return redirect(url_for("auth.login_page"))


@auth_bp.route("/logout")
def logout_user():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("auth.login_page"))


@auth_bp.route("/send-otp", methods=["POST"])
def send_otp():
    email = request.form.get("email", "").strip().lower()

    result = send_password_reset_otp(email)

    if isinstance(result, str):
        flash(result)
        return redirect(url_for("auth.login_page"))

    session["reset_otp"]      = result["otp"]
    session["reset_email"]    = result["email"]
    session["reset_otp_time"] = datetime.utcnow().isoformat()

    if current_app.config.get("DEBUG"):
        flash(
            f"[DEV] Your OTP is: {result['otp']}  (shown only in DEBUG mode)",
            "success",
        )
    else:
        flash(f"A 6-digit OTP has been sent to {result['email']}.", "success")

    redirect_url = url_for("auth.login_page") + f"?mode=otp&email={result['email']}"
    return redirect(redirect_url)


@auth_bp.route("/reset-password", methods=["POST"])
def do_reset_password():
    email                = request.form.get("email",                "").strip().lower()
    submitted_otp        = request.form.get("otp",                  "").strip()
    new_password         = request.form.get("new_password",         "")
    confirm_new_password = request.form.get("confirm_new_password", "")

    stored_otp    = session.get("reset_otp")
    otp_time_str  = session.get("reset_otp_time")
    session_email = session.get("reset_email", "")

    if email != session_email:
        flash("Session mismatch. Please request a new OTP.")
        return redirect(url_for("auth.login_page"))

    result = reset_user_password(
        email,
        submitted_otp,
        stored_otp,
        otp_time_str,
        new_password,
        confirm_new_password,
    )

    if isinstance(result, str):
        flash(result)
        redirect_url = url_for("auth.login_page") + f"?mode=otp&email={email}"
        return redirect(redirect_url)

    session.pop("reset_otp",      None)
    session.pop("reset_email",    None)
    session.pop("reset_otp_time", None)

    flash("Password reset successfully! Please sign in with your new password.", "success")
    return redirect(url_for("auth.login_page"))
