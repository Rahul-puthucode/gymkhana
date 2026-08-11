from flask import Blueprint, render_template, session, redirect, url_for
from utils.database import query_db
from utils.auth import login_required, role_required
from utils.helpers import calculate_remaining_days, calculate_bmi

member_bp = Blueprint('member', __name__, url_prefix='/member')

@member_bp.route('/dashboard')
@login_required
@role_required('MEMBER')
def dashboard():
    member_id = session.get('user_id')
    user = query_db("SELECT * FROM users WHERE id = %s", (member_id,), one=True)
    if not user:
        session.clear()
        return redirect(url_for('auth.login'))
    
    # 1. Membership Status
    subscription = query_db(
        """SELECT s.*, p.name as plan_name, p.duration_months
           FROM subscriptions s
           JOIN membership_plans p ON s.plan_id = p.id
           WHERE s.member_id = %s
           ORDER BY s.id DESC LIMIT 1""",
        (member_id,), one=True
    )
    
    remaining_days = 0
    status_label = "No Plan"
    if subscription:
        remaining_days = calculate_remaining_days(subscription['expiry_date'])
        if remaining_days <= 0:
            status_label = "Expired"
        elif remaining_days <= 7:
            status_label = "Expiring Soon"
        else:
            status_label = "Active"

    # 2. Fitness Summary
    latest_progress = query_db(
        "SELECT * FROM fitness_progress WHERE member_id = %s ORDER BY recorded_at DESC, id DESC LIMIT 1",
        (member_id,), one=True
    )
    
    current_weight = user.get('weight') or (latest_progress['weight'] if latest_progress else '--')
    current_height = user.get('height') or (latest_progress['height'] if latest_progress else '--')
    
    bmi, bmi_category = 0.0, "N/A"
    if current_weight != '--' and current_height != '--' and float(current_height) > 0:
        bmi, bmi_category = calculate_bmi(current_weight, current_height)

    # 3. Active Workout Plan & Today's Exercises
    workout_plan = query_db(
        "SELECT * FROM workout_plans WHERE member_id = %s AND status = 'active' ORDER BY id DESC LIMIT 1",
        (member_id,), one=True
    )
    
    today_exercises = []
    completion_pct = 0
    if workout_plan:
        today_exercises = query_db(
            """SELECT we.*, e.name as exercise_name, e.muscle_group, e.equipment,
                      COALESCE(wp.completed, 0) as is_completed, wp.actual_weight, wp.actual_reps
               FROM workout_exercises we
               JOIN exercises e ON we.exercise_id = e.id
               LEFT JOIN workout_progress wp ON wp.workout_exercise_id = we.id AND wp.member_id = %s AND wp.completed_at = CURRENT_DATE
               WHERE we.workout_plan_id = %s
               ORDER BY we.id ASC""",
            (member_id, workout_plan['id'])
        )
        
        if today_exercises:
            completed_count = sum(1 for ex in today_exercises if ex['is_completed'])
            completion_pct = round((completed_count / len(today_exercises)) * 100)

    # 4. Active Diet Plan & Meals
    diet_plan = query_db(
        "SELECT * FROM diet_plans WHERE member_id = %s AND status = 'active' ORDER BY id DESC LIMIT 1",
        (member_id,), one=True
    )
    
    meals = []
    if diet_plan:
        meals = query_db("SELECT * FROM diet_meals WHERE diet_plan_id = %s", (diet_plan['id'],))

    # 5. Weight progress history for Chart.js
    weight_history = query_db(
        "SELECT weight, recorded_at FROM fitness_progress WHERE member_id = %s ORDER BY recorded_at ASC LIMIT 10",
        (member_id,)
    )

    # 6. Recent Notifications
    notifications = query_db(
        "SELECT * FROM notifications WHERE user_id = %s ORDER BY created_at DESC LIMIT 5",
        (member_id,)
    )

    return render_template(
        'member/dashboard.html',
        user=user,
        subscription=subscription,
        remaining_days=remaining_days,
        status_label=status_label,
        latest_progress=latest_progress,
        current_weight=current_weight,
        current_height=current_height,
        bmi=bmi,
        bmi_category=bmi_category,
        workout_plan=workout_plan,
        today_exercises=today_exercises,
        completion_pct=completion_pct,
        diet_plan=diet_plan,
        meals=meals,
        weight_history=weight_history,
        notifications=notifications
    )
