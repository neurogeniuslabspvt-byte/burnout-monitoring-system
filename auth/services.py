from __future__ import annotations

import random
import re
import string
from datetime import datetime, timedelta

from werkzeug.security import generate_password_hash, check_password_hash

from auth.repository import (
    find_user_by_email,
    email_exists,
    employee_id_exists,
    manager_id_exists,
    insert_user,
    create_employee_and_user,
    update_user_password,
)

_SPECIAL_RE = re.compile(r'[!@#$%^&*()\-_=+\[\]{}|;:\'",.<>?\/\\~`]')


def hash_password(password: str) -> str:
    return generate_password_hash(password)


def verify_password(password: str, stored_hash: str) -> bool:
    return check_password_hash(stored_hash, password)


def authenticate_user(email: str, password: str) -> dict | str:
    if not email or not email.strip():
        return "Email is required."
    if not password:
        return "Password is required."

    user = find_user_by_email(email)
    if user is None:
        return "Invalid email or password."
    if not verify_password(password, user["password_hash"]):
        return "Invalid email or password."
    return user


def _validate_employee_id(value: str) -> str | None:
    if len(value) != 8:
        return f"Employee ID must be exactly 8 characters (you entered {len(value)})."
    if not re.search(r'[a-zA-Z]', value):
        return "Employee ID must contain at least one letter."
    if not re.search(r'[0-9]', value):
        return "Employee ID must contain at least one number."
    if not _SPECIAL_RE.search(value):
        return "Employee ID must contain at least one special character."
    return None


def _validate_manager_id(value: str) -> str | None:
    """
    Validate Manager Employee ID — same format rules as employee IDs:
    exactly 8 characters containing at least one letter, one number,
    and one special character.
    """
    if len(value) != 8:
        return f"Manager Employee ID must be exactly 8 characters (you entered {len(value)})."
    if not re.search(r'[a-zA-Z]', value):
        return "Manager Employee ID must contain at least one letter."
    if not re.search(r'[0-9]', value):
        return "Manager Employee ID must contain at least one number."
    if not _SPECIAL_RE.search(value):
        return "Manager Employee ID must contain at least one special character."
    return None


def _validate_password_strength(password: str) -> str | None:
    if len(password) < 10:
        return "Password must be at least 10 characters long."
    if not re.search(r'[A-Z]', password):
        return "Password must contain at least one uppercase letter."
    if not re.search(r'[a-z]', password):
        return "Password must contain at least one lowercase letter."
    if not re.search(r'[0-9]', password):
        return "Password must contain at least one number."
    if not _SPECIAL_RE.search(password):
        return "Password must contain at least one special character."
    return None


def _validate_email_format(email: str) -> str | None:
    if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]{2,}$', email):
        return "Enter a valid email address."
    return None


def create_new_user(data: dict) -> int | str:
    role = data.get("role", "employee").strip().lower()
    if role not in ("employee", "manager"):
        return "Invalid role selected."

    # Fields required for both roles
    for field in ("name", "email", "password", "confirm_password"):
        if not data.get(field) or not str(data[field]).strip():
            return f"{field.replace('_', ' ').capitalize()} is required."

    name             = data["name"].strip()
    email            = data["email"].strip().lower()
    password         = data["password"]
    confirm_password = data["confirm_password"]

    email_error = _validate_email_format(email)
    if email_error:
        return email_error

    pw_error = _validate_password_strength(password)
    if pw_error:
        return pw_error

    if password != confirm_password:
        return "Passwords do not match."

    if email_exists(email):
        return "An account with this email already exists."

    password_hash = hash_password(password)

    # ── Manager path ──────────────────────────────────────────────────────
    if role == "manager":
        manager_id = data.get("manager_id", "").strip()

        if not manager_id:
            return "Manager Employee ID is required."

        id_error = _validate_manager_id(manager_id)
        if id_error:
            return id_error

        if manager_id_exists(manager_id):
            return "This Manager Employee ID is already registered."

        new_id = insert_user({
            "name":          name,
            "email":         email,
            "password_hash": password_hash,
            "role":          "manager",
            "employee_id":   None,      # managers have no employees row
            "manager_id":    manager_id,
        })
        return new_id

    # ── Employee path ─────────────────────────────────────────────────────
    employee_id   = data.get("employee_id", "").strip()
    department_id = data.get("department_id") or None

    if not employee_id:
        return "Employee ID is required."

    id_error = _validate_employee_id(employee_id)
    if id_error:
        return id_error

    if employee_id_exists(employee_id):
        return "This Employee ID is already registered."

    new_id = create_employee_and_user(
        employee_data={
            "id":            employee_id,
            "name":          name,
            "email":         email,
            "department_id": int(department_id) if department_id else None,
        },
        user_data={
            "name":          name,
            "email":         email,
            "password_hash": password_hash,
        },
    )
    return new_id


def generate_otp() -> str:
    return "".join(random.choices(string.digits, k=6))


def send_password_reset_otp(email: str) -> dict | str:
    if not email or not email.strip():
        return "Email is required."
    user = find_user_by_email(email.strip().lower())
    if user is None:
        return "No account found with this email address."
    otp = generate_otp()
    return {"otp": otp, "email": email.strip().lower()}


def reset_user_password(
    email: str,
    submitted_otp: str,
    stored_otp: str | None,
    otp_time_str: str | None,
    new_password: str,
    confirm_new_password: str,
) -> bool | str:
    if not stored_otp or not otp_time_str:
        return "OTP session expired. Please request a new one."

    otp_time = datetime.fromisoformat(otp_time_str)
    if datetime.utcnow() - otp_time > timedelta(minutes=10):
        return "OTP has expired. Please request a new one."

    if submitted_otp != stored_otp:
        return "Invalid OTP. Please try again."

    pw_error = _validate_password_strength(new_password)
    if pw_error:
        return pw_error

    if new_password != confirm_new_password:
        return "Passwords do not match."

    update_user_password(email, hash_password(new_password))
    return True
