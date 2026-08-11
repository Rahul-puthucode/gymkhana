from functools import wraps
from flask import session, redirect, url_for, flash, request
from werkzeug.security import generate_password_hash, check_password_hash

def hash_password(password):
    return generate_password_hash(password)

def verify_password(hashed_password, password):
    return check_password_hash(hashed_password, password)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def role_required(*allowed_roles):
    """
    Decorator to restrict access based on user role name.
    Usage: @role_required('ADMIN') or @role_required('MEMBER', 'TRAINER')
    """
    # Accept either unpack args or list
    if len(allowed_roles) == 1 and isinstance(allowed_roles[0], (list, tuple)):
        roles_list = [r.upper() for r in allowed_roles[0]]
    else:
        roles_list = [r.upper() for r in allowed_roles]

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('auth.login', next=request.url))
            
            user_role = session.get('user_role', '').upper()
            if user_role not in roles_list:
                flash('Access denied: You do not have permission to view this resource.', 'danger')
                return redirect(url_for('auth.unauthorized'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator
