from flask import Blueprint, render_template, redirect, url_for, request, session, flash

from .repository import save_survey_response, get_today_response
from .services   import check_today_submission

from services.ml_api_client   import predict_burnout
from services.history_service import get_week_history
from utils.validation_utils   import validate_survey_inputs, sanitize_inputs, validate_employee_id
from auth.decorators import employee_required

employee_bp = Blueprint('employee', __name__, url_prefix='/employee')


@employee_bp.route('/survey')
@employee_required
def show_survey():
    employee_id = session['employee_id']
    if check_today_submission(employee_id):
        return redirect(url_for('employee.employee_dashboard'))
    return render_template('employee/survey.html')


@employee_bp.route('/submit-survey', methods=['POST'])
@employee_required
def submit_survey():
    employee_id = session['employee_id']

    emp_check = validate_employee_id(employee_id)
    if emp_check is not True:
        flash(emp_check)
        return redirect(url_for('auth.login_page'))

    if check_today_submission(employee_id):
        return redirect(url_for('employee.employee_dashboard'))

    raw = {
        'happiness':  request.form.get('happiness'),
        'motivation': request.form.get('motivation'),
        'stress':     request.form.get('stress'),
        'caffeine':   request.form.get('caffeine'),
    }

    validation_result = validate_survey_inputs(raw)
    if validation_result is not True:
        flash(validation_result)
        return redirect(url_for('employee.show_survey'))

    happiness, motivation, stress, caffeine = sanitize_inputs(raw)

    burnout_score, burnout_label = predict_burnout({
        'happiness':  happiness,
        'motivation': motivation,
        'stress':     stress,
        'caffeine':   caffeine,
    })

    save_survey_response(
        employee_id=employee_id,
        happiness=happiness,
        motivation=motivation,
        stress=stress,
        caffeine=caffeine,
        burnout_score=burnout_score,
        burnout_label=burnout_label,
    )

    return redirect(url_for('employee.employee_dashboard'))


@employee_bp.route('/dashboard')
@employee_required
def employee_dashboard():
    employee_id = session['employee_id']
    submitted   = check_today_submission(employee_id)

    burnout_score = '--'
    burnout_label = '--'

    if submitted:
        record = get_today_response(employee_id)
        if record is not None and record['burnout_score'] is not None:
            burnout_score = record['burnout_score']
            burnout_label = record['burnout_label']

    return render_template(
        'employee/dashboard.html',
        submitted=submitted,
        burnout_score=burnout_score,
        burnout_label=burnout_label,
    )


@employee_bp.route('/history')
@employee_required
def employee_history():
    employee_id = session['employee_id']
    history_scores, history_labels, avg_score = get_week_history(employee_id)

    return render_template(
        'employee/history.html',
        history_scores=history_scores,
        history_labels=history_labels,
        avg_score=avg_score,
    )
