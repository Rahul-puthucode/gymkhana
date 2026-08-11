from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from utils.database import query_db, execute_db
from utils.auth import login_required, role_required
from utils.helpers import calculate_bmi, log_activity

progress_bp = Blueprint('progress', __name__, url_prefix='/progress')

@progress_bp.route('/')
@login_required
@role_required('MEMBER')
def index():
    member_id = session.get('user_id')
    user = query_db("SELECT * FROM users WHERE id = %s", (member_id,), one=True)
    if not user:
        session.clear()
        return redirect(url_for('auth.login'))
    
    # Progress records sorted chronologically for charts, and newest-first for table
    records_desc = query_db(
        "SELECT * FROM fitness_progress WHERE member_id = %s ORDER BY recorded_at DESC, id DESC",
        (member_id,)
    )
    
    records_asc = query_db(
        "SELECT * FROM fitness_progress WHERE member_id = %s ORDER BY recorded_at ASC, id ASC",
        (member_id,)
    )

    latest = records_desc[0] if records_desc else None
    
    current_bmi, current_category = 0.0, "N/A"
    if latest:
        current_bmi, current_category = calculate_bmi(latest['weight'], latest['height'])
    elif user.get('weight') and user.get('height'):
        current_bmi, current_category = calculate_bmi(user['weight'], user['height'])

    return render_template(
        'member/progress.html',
        user=user,
        records_desc=records_desc,
        records_asc=records_asc,
        latest=latest,
        current_bmi=current_bmi,
        current_category=current_category
    )

@progress_bp.route('/add', methods=['POST'])
@login_required
@role_required('MEMBER')
def add():
    member_id = session.get('user_id')
    weight = request.form.get('weight', type=float)
    height = request.form.get('height', type=float)
    chest = request.form.get('chest', type=float)
    waist = request.form.get('waist', type=float)
    arms = request.form.get('arms', type=float)
    thighs = request.form.get('thighs', type=float)
    recorded_at = request.form.get('recorded_at')

    if not weight or not height or height <= 0:
        flash('Valid weight and height are required.', 'danger')
        return redirect(url_for('progress.index'))

    bmi, category = calculate_bmi(weight, height)

    execute_db(
        """INSERT INTO fitness_progress (member_id, weight, height, bmi, chest, waist, arms, thighs, recorded_at)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
        (member_id, weight, height, bmi, chest or None, waist or None, arms or None, thighs or None, recorded_at)
    )

    # Update user height/weight in profile
    execute_db("UPDATE users SET height = %s, weight = %s WHERE id = %s", (height, weight, member_id))

    log_activity(member_id, 'MEMBER', 'FITNESS_PROGRESS_ADDED', f"Logged weight {weight} kg, BMI {bmi}")
    flash(f"Progress recorded successfully! BMI: {bmi} ({category})", 'success')
    return redirect(url_for('progress.index'))
