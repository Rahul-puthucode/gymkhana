from datetime import date
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from utils.database import query_db, execute_db
from utils.auth import login_required, role_required
from utils.helpers import calculate_remaining_days, calculate_bmi, log_activity, send_notification

trainer_bp = Blueprint('trainer', __name__, url_prefix='/trainer')

@trainer_bp.route('/dashboard')
@login_required
@role_required('TRAINER')
def dashboard():
    trainer_user_id = session.get('user_id')
    
    # Fetch assigned members (members who have workout or diet plans assigned by this trainer or assigned directly)
    members = query_db(
        """SELECT DISTINCT u.*, 
                  (SELECT s.status FROM subscriptions s WHERE s.member_id = u.id ORDER BY s.id DESC LIMIT 1) as sub_status,
                  (SELECT MAX(recorded_at) FROM fitness_progress fp WHERE fp.member_id = u.id) as last_progress_date
           FROM users u
           JOIN roles r ON u.role_id = r.id
           LEFT JOIN workout_plans wp ON wp.member_id = u.id AND wp.trainer_id = %s
           LEFT JOIN diet_plans dp ON dp.member_id = u.id AND dp.trainer_id = %s
           WHERE LOWER(r.name) = 'member' AND (wp.trainer_id = %s OR dp.trainer_id = %s)""",
        (trainer_user_id, trainer_user_id, trainer_user_id, trainer_user_id)
    )
    
    total_assigned = len(members)
    active_members = sum(1 for m in members if m.get('sub_status') == 'active')
    
    workout_plans_count = query_db(
        "SELECT COUNT(*) as cnt FROM workout_plans WHERE trainer_id = %s AND status = 'active'",
        (trainer_user_id,), one=True
    )['cnt']

    diet_plans_count = query_db(
        "SELECT COUNT(*) as cnt FROM diet_plans WHERE trainer_id = %s AND status = 'active'",
        (trainer_user_id,), one=True
    )['cnt']

    # Recent workout completions
    recent_activity = query_db(
        """SELECT wp.*, u.name as member_name, e.name as exercise_name
           FROM workout_progress wp
           JOIN users u ON wp.member_id = u.id
           JOIN workout_exercises we ON wp.workout_exercise_id = we.id
           JOIN exercises e ON we.exercise_id = e.id
           ORDER BY wp.completed_at DESC, wp.id DESC LIMIT 5"""
    )

    return render_template(
        'trainer/dashboard.html',
        total_assigned=total_assigned,
        active_members=active_members,
        workout_plans_count=workout_plans_count,
        diet_plans_count=diet_plans_count,
        members=members[:5],
        recent_activity=recent_activity
    )

@trainer_bp.route('/my-members')
@login_required
@role_required('TRAINER')
def my_members():
    trainer_user_id = session.get('user_id')
    search = request.args.get('q', '').strip()
    
    query = """SELECT DISTINCT u.*, 
                      (SELECT s.status FROM subscriptions s WHERE s.member_id = u.id ORDER BY s.id DESC LIMIT 1) as sub_status,
                      (SELECT p.name FROM subscriptions s JOIN membership_plans p ON s.plan_id = p.id WHERE s.member_id = u.id ORDER BY s.id DESC LIMIT 1) as plan_name
               FROM users u
               JOIN roles r ON u.role_id = r.id
               WHERE LOWER(r.name) = 'member'"""
    
    params = []
    if search:
        query += " AND (LOWER(u.name) LIKE %s OR LOWER(u.email) LIKE %s OR u.phone LIKE %s)"
        s_param = f"%{search.lower()}%"
        params.extend([s_param, s_param, s_param])
        
    query += " ORDER BY u.name ASC"
    members = query_db(query, tuple(params))

    return render_template('trainer/my_members.html', members=members, search=search)

@trainer_bp.route('/member/<int:member_id>')
@login_required
@role_required('TRAINER')
def member_detail(member_id):
    trainer_user_id = session.get('user_id')
    member = query_db("SELECT * FROM users WHERE id = %s", (member_id,), one=True)
    if not member:
        flash('Member not found.', 'danger')
        return redirect(url_for('trainer.my_members'))

    # Subscription details
    subscription = query_db(
        """SELECT s.*, p.name as plan_name 
           FROM subscriptions s 
           JOIN membership_plans p ON s.plan_id = p.id 
           WHERE s.member_id = %s ORDER BY s.id DESC LIMIT 1""",
        (member_id,), one=True
    )
    
    # Active Workout Plan
    workout_plan = query_db(
        "SELECT * FROM workout_plans WHERE member_id = %s AND status = 'active' ORDER BY id DESC LIMIT 1",
        (member_id,), one=True
    )
    workout_exercises = []
    if workout_plan:
        workout_exercises = query_db(
            """SELECT we.*, e.name as exercise_name, e.muscle_group 
               FROM workout_exercises we 
               JOIN exercises e ON we.exercise_id = e.id 
               WHERE we.workout_plan_id = %s ORDER BY we.day, we.id""",
            (workout_plan['id'],)
        )

    # Active Diet Plan
    diet_plan = query_db(
        "SELECT * FROM diet_plans WHERE member_id = %s AND status = 'active' ORDER BY id DESC LIMIT 1",
        (member_id,), one=True
    )
    diet_meals = []
    if diet_plan:
        diet_meals = query_db("SELECT * FROM diet_meals WHERE diet_plan_id = %s ORDER BY id", (diet_plan['id'],))

    # Fitness progress history
    progress_history = query_db(
        "SELECT * FROM fitness_progress WHERE member_id = %s ORDER BY recorded_at DESC",
        (member_id,)
    )

    bmi, bmi_category = calculate_bmi(member.get('weight'), member.get('height'))
    exercises_list = query_db("SELECT * FROM exercises ORDER BY muscle_group, name")

    return render_template(
        'trainer/member_detail.html',
        member=member,
        subscription=subscription,
        workout_plan=workout_plan,
        workout_exercises=workout_exercises,
        diet_plan=diet_plan,
        diet_meals=diet_meals,
        progress_history=progress_history,
        bmi=bmi,
        bmi_category=bmi_category,
        exercises_list=exercises_list
    )

@trainer_bp.route('/assign-workout', methods=['POST'])
@login_required
@role_required('TRAINER')
def assign_workout():
    trainer_id = session.get('user_id')
    member_id = request.form.get('member_id', type=int)
    plan_name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')

    if not member_id or not plan_name or not start_date or not end_date:
        flash('Please fill in all required workout plan fields.', 'danger')
        return redirect(url_for('trainer.my_members'))

    # Deactivate existing active plans
    execute_db("UPDATE workout_plans SET status = 'inactive' WHERE member_id = %s", (member_id,))

    # Insert plan
    plan_id = execute_db(
        """INSERT INTO workout_plans (member_id, trainer_id, name, description, start_date, end_date, status)
           VALUES (%s, %s, %s, %s, %s, %s, 'active')""",
        (member_id, trainer_id, plan_name, description, start_date, end_date)
    )

    # Process exercises
    exercise_ids = request.form.getlist('exercise_id[]')
    days = request.form.getlist('day[]')
    sets_list = request.form.getlist('sets[]')
    reps_list = request.form.getlist('reps[]')
    weights = request.form.getlist('weight[]')
    rests = request.form.getlist('rest_seconds[]')

    for i in range(len(exercise_ids)):
        if exercise_ids[i]:
            execute_db(
                """INSERT INTO workout_exercises (workout_plan_id, exercise_id, day, sets, reps, weight, rest_seconds)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                (plan_id, int(exercise_ids[i]), days[i], int(sets_list[i]), reps_list[i], weights[i], int(rests[i] or 60))
            )

    log_activity(trainer_id, 'TRAINER', 'WORKOUT_ASSIGNED', f"Assigned workout plan '{plan_name}' to member ID #{member_id}")
    send_notification(member_id, "New Workout Plan Assigned!", f"Your trainer assigned a new workout plan: {plan_name}.", "info")
    
    flash(f"Workout plan '{plan_name}' successfully assigned to member!", 'success')
    return redirect(url_for('trainer.member_detail', member_id=member_id))

@trainer_bp.route('/assign-diet', methods=['POST'])
@login_required
@role_required('TRAINER')
def assign_diet():
    trainer_id = session.get('user_id')
    member_id = request.form.get('member_id', type=int)
    plan_name = request.form.get('name', '').strip()
    goal = request.form.get('goal', '').strip()
    calories = request.form.get('calories', type=int)
    protein = request.form.get('protein', type=int)
    carbs = request.form.get('carbohydrates', type=int)
    fat = request.form.get('fat', type=int)
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')

    if not member_id or not plan_name or not calories:
        flash('Please fill in required diet plan details.', 'danger')
        return redirect(url_for('trainer.my_members'))

    # Deactivate active diet plans
    execute_db("UPDATE diet_plans SET status = 'inactive' WHERE member_id = %s", (member_id,))

    plan_id = execute_db(
        """INSERT INTO diet_plans (member_id, trainer_id, name, goal, calories, protein, carbohydrates, fat, start_date, end_date, status)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'active')""",
        (member_id, trainer_id, plan_name, goal, calories, protein or 0, carbs or 0, fat or 0, start_date, end_date)
    )

    # Insert meals
    meal_types = request.form.getlist('meal_type[]')
    food_names = request.form.getlist('food_name[]')
    quantities = request.form.getlist('quantity[]')
    meal_cals = request.form.getlist('meal_calories[]')
    meal_prots = request.form.getlist('meal_protein[]')
    meal_carbs = request.form.getlist('meal_carbs[]')
    meal_fats = request.form.getlist('meal_fat[]')

    for i in range(len(food_names)):
        if food_names[i]:
            execute_db(
                """INSERT INTO diet_meals (diet_plan_id, meal_type, food_name, quantity, calories, protein, carbohydrates, fat)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                (plan_id, meal_types[i], food_names[i], quantities[i], int(meal_cals[i] or 0), 
                 int(meal_prots[i] or 0), int(meal_carbs[i] or 0), int(meal_fats[i] or 0))
            )

    log_activity(trainer_id, 'TRAINER', 'DIET_ASSIGNED', f"Assigned diet plan '{plan_name}' to member ID #{member_id}")
    send_notification(member_id, "New Diet Plan Assigned!", f"Your trainer assigned a new diet plan: {plan_name}.", "info")

    flash(f"Diet plan '{plan_name}' successfully assigned to member!", 'success')
    return redirect(url_for('trainer.member_detail', member_id=member_id))

@trainer_bp.route('/workout-plans')
@login_required
@role_required('TRAINER')
def workout_plans():
    trainer_id = session.get('user_id')
    plans = query_db(
        """SELECT wp.*, u.name as member_name 
           FROM workout_plans wp 
           JOIN users u ON wp.member_id = u.id 
           WHERE wp.trainer_id = %s ORDER BY wp.created_at DESC""",
        (trainer_id,)
    )
    return render_template('trainer/workout_plans.html', plans=plans)

@trainer_bp.route('/diet-plans')
@login_required
@role_required('TRAINER')
def diet_plans():
    trainer_id = session.get('user_id')
    plans = query_db(
        """SELECT dp.*, u.name as member_name 
           FROM diet_plans dp 
           JOIN users u ON dp.member_id = u.id 
           WHERE dp.trainer_id = %s ORDER BY dp.id DESC""",
        (trainer_id,)
    )
    return render_template('trainer/diet_plans.html', plans=plans)

@trainer_bp.route('/member-progress')
@login_required
@role_required('TRAINER')
def member_progress():
    trainer_id = session.get('user_id')
    progress_list = query_db(
        """SELECT fp.*, u.name as member_name, u.email 
           FROM fitness_progress fp 
           JOIN users u ON fp.member_id = u.id 
           ORDER BY fp.recorded_at DESC LIMIT 30"""
    )
    return render_template('trainer/member_progress.html', progress_list=progress_list)
