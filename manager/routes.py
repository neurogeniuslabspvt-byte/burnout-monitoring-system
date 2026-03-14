from __future__ import annotations
from flask import Blueprint, render_template, abort

from manager.services import (
    get_employee_burnout_list,
    get_employee_burnout_trend,
    get_dashboard_summary,
)
from auth.decorators import manager_required

manager_bp = Blueprint("manager", __name__, url_prefix="/manager")


@manager_bp.route("/dashboard")
@manager_required
def manager_dashboard():
    summary = get_dashboard_summary()
    return render_template(
        "manager/dashboard.html",
        distribution  = summary["distribution"],
        avg_score     = summary["avg_score"],
        trend_labels  = summary["trend_labels"],
        trend_scores  = summary["trend_scores"],
        high_risk     = summary["high_risk"],
    )


@manager_bp.route("/employees")
@manager_required
def employee_list():
    employees = get_employee_burnout_list()
    return render_template("manager/employees.html", employees=employees)


@manager_bp.route("/employee/<employee_id>")
@manager_required
def employee_detail(employee_id: str):
    trend = get_employee_burnout_trend(employee_id)
    if not trend["employee"]["name"]:
        abort(404)
    return render_template("manager/employee_detail.html", trend=trend)
