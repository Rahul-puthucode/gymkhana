import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from werkzeug.utils import secure_filename
from utils.database import query_db, execute_db
from utils.auth import hash_password, verify_password, login_required
from utils.helpers import log_activity, calculate_bmi

auth_bp = Blueprint('auth', __name__)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect_by_role(session.get('user_role'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        gender = request.form.get('gender', '')
        date_of_birth = request.form.get('date_of_birth', None)
        height = request.form.get('height', None)
        weight = request.form.get('weight', None)

        # Validation
        if not name or not email or not password:
            flash('Full Name, Email, and Password are required fields.', 'danger')
            return render_template('auth/register.html')

        if password != confirm_password:
            flash('Passwords do not match. Please try again.', 'danger')
            return render_template('auth/register.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return render_template('auth/register.html')

        # Check existing user
        existing_user = query_db("SELECT id FROM users WHERE email = %s", (email,), one=True)
        if existing_user:
            flash('An account with this email address already exists.', 'warning')
            return render_template('auth/register.html')

        # Get Member role ID (default = 1)
        role = query_db("SELECT id FROM roles WHERE LOWER(name) = 'member'", one=True)
        role_id = role['id'] if role else 1

        hashed_pwd = hash_password(password)

        # Insert user
        user_id = execute_db(
            """INSERT INTO users 
               (role_id, name, email, password_hash, phone, gender, date_of_birth, height, weight, status) 
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'active')""",
            (role_id, name, email, hashed_pwd, phone, gender, date_of_birth or None, height or None, weight or None)
        )

        # Add initial fitness progress entry if weight & height provided
        if weight and height and float(height) > 0 and float(weight) > 0:
            bmi, _ = calculate_bmi(weight, height)
            execute_db(
                """INSERT INTO fitness_progress (member_id, weight, height, bmi, recorded_at)
                   VALUES (%s, %s, %s, %s, CURRENT_DATE)""",
                (user_id, weight, height, bmi)
            )

        log_activity(user_id, 'MEMBER', 'USER_REGISTERED', f"New member registered: {email}")

        # Send welcome notification
        execute_db(
            "INSERT INTO notifications (user_id, title, message, type) VALUES (%s, %s, %s, %s)",
            (user_id, "Welcome to Gymkhana!", "Thank you for registering. Explore membership plans to get started.", "info")
        )

        flash('Registration successful! Please log in to continue.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect_by_role(session.get('user_role'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not email or not password:
            flash('Please provide both email and password.', 'danger')
            return render_template('auth/login.html')

        user = query_db(
            """SELECT u.*, r.name as role_name 
               FROM users u 
               JOIN roles r ON u.role_id = r.id 
               WHERE u.email = %s""", 
            (email,), one=True
        )

        if not user or not verify_password(user['password_hash'], password):
            flash('Invalid email address or password.', 'danger')
            return render_template('auth/login.html')

        if user.get('status') != 'active':
            flash('Your account has been deactivated. Please contact administration.', 'danger')
            return render_template('auth/login.html')

        # Set session
        session['user_id'] = user['id']
        session['user_name'] = user['name']
        session['user_email'] = user['email']
        session['user_role'] = user['role_name'].upper()
        session['user_image'] = user.get('profile_image', 'default_profile.png')

        log_activity(user['id'], user['role_name'].upper(), 'USER_LOGIN', f"User logged in: {email}")

        flash(f"Welcome back, {user['name']}!", 'success')
        return redirect_by_role(user['role_name'].upper())

    return render_template('auth/login.html')

@auth_bp.route('/logout')
def logout():
    user_id = session.get('user_id')
    role = session.get('user_role')
    email = session.get('user_email')
    
    if user_id:
        log_activity(user_id, role, 'USER_LOGOUT', f"User logged out: {email}")
        
    session.clear()
    flash('You have been successfully logged out.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user_id = session.get('user_id')
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        gender = request.form.get('gender', '')
        date_of_birth = request.form.get('date_of_birth', None)
        height = request.form.get('height', None)
        weight = request.form.get('weight', None)
        address = request.form.get('address', '').strip()
        emergency_contact = request.form.get('emergency_contact', '').strip()

        # Profile image upload
        profile_image = session.get('user_image', 'default_profile.png')
        if 'profile_photo' in request.files:
            file = request.files['profile_photo']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(f"user_{user_id}_{file.filename}")
                upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'profiles')
                os.makedirs(upload_path, exist_ok=True)
                file.save(os.path.join(upload_path, filename))
                profile_image = filename
                session['user_image'] = profile_image

        execute_db(
            """UPDATE users 
               SET name = %s, phone = %s, gender = %s, date_of_birth = %s, 
                   height = %s, weight = %s, address = %s, emergency_contact = %s, profile_image = %s
               WHERE id = %s""",
            (name, phone, gender, date_of_birth or None, height or None, weight or None, 
             address, emergency_contact, profile_image, user_id)
        )

        session['user_name'] = name

        # Record progress if weight/height updated for member
        if session.get('user_role') == 'MEMBER' and weight and height and float(height) > 0 and float(weight) > 0:
            bmi, _ = calculate_bmi(weight, height)
            execute_db(
                """INSERT INTO fitness_progress (member_id, weight, height, bmi, recorded_at)
                   VALUES (%s, %s, %s, %s, CURRENT_DATE)""",
                (user_id, weight, height, bmi)
            )

        log_activity(user_id, session.get('user_role'), 'PROFILE_UPDATE', f"Updated profile information")
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('auth.profile'))

    user = query_db("SELECT * FROM users WHERE id = %s", (user_id,), one=True)
    return render_template('auth/profile.html', user=user)

@auth_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    user_id = session.get('user_id')
    current_pwd = request.form.get('current_password', '')
    new_pwd = request.form.get('new_password', '')
    confirm_pwd = request.form.get('confirm_password', '')

    user = query_db("SELECT password_hash FROM users WHERE id = %s", (user_id,), one=True)
    
    if not verify_password(user['password_hash'], current_pwd):
        flash('Current password is incorrect.', 'danger')
        return redirect(url_for('auth.profile'))

    if new_pwd != confirm_pwd:
        flash('New password and confirmation do not match.', 'danger')
        return redirect(url_for('auth.profile'))

    if len(new_pwd) < 6:
        flash('New password must be at least 6 characters long.', 'danger')
        return redirect(url_for('auth.profile'))

    hashed_pwd = hash_password(new_pwd)
    execute_db("UPDATE users SET password_hash = %s WHERE id = %s", (hashed_pwd, user_id))

    log_activity(user_id, session.get('user_role'), 'PASSWORD_CHANGE', 'Changed account password')
    flash('Password changed successfully!', 'success')
    return redirect(url_for('auth.profile'))

@auth_bp.route('/unauthorized')
def unauthorized():
    return render_template('errors/403.html'), 403

def redirect_by_role(role_name):
    if not role_name:
        return redirect(url_for('auth.login'))
    
    r = role_name.upper()
    if r == 'ADMIN':
        return redirect(url_for('admin.dashboard'))
    elif r == 'TRAINER':
        return redirect(url_for('trainer.dashboard'))
    else:
        return redirect(url_for('member.dashboard'))
