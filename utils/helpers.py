from datetime import datetime, date
from utils.database import execute_db, query_db

def calculate_bmi(weight_kg, height_cm):
    """Calculate BMI from weight in kg and height in cm."""
    if not weight_kg or not height_cm or float(height_cm) <= 0:
        return 0.0, "Unknown"
    
    w = float(weight_kg)
    h_m = float(height_cm) / 100.0
    bmi = round(w / (h_m * h_m), 2)
    
    if bmi < 18.5:
        category = "Underweight"
    elif 18.5 <= bmi <= 24.9:
        category = "Normal"
    elif 25.0 <= bmi <= 29.9:
        category = "Overweight"
    else:
        category = "Obese"
        
    return bmi, category

def calculate_remaining_days(expiry_date):
    """Calculate days remaining until expiry_date."""
    if not expiry_date:
        return 0
    if isinstance(expiry_date, str):
        try:
            expiry_date = datetime.strptime(expiry_date, '%Y-%m-%d').date()
        except ValueError:
            return 0
    elif isinstance(expiry_date, datetime):
        expiry_date = expiry_date.date()
        
    today = date.today()
    delta = (expiry_date - today).days
    return max(0, delta)

def log_activity(user_id, role, action, description):
    """Record an audit trail activity log entry in database."""
    try:
        execute_db(
            "INSERT INTO activity_logs (user_id, role, action, description) VALUES (%s, %s, %s, %s)",
            (user_id, role, action, description)
        )
    except Exception as e:
        print(f"Error recording activity log: {e}")

def send_notification(user_id, title, message, notif_type='info'):
    """Create an in-app notification for a user."""
    try:
        execute_db(
            "INSERT INTO notifications (user_id, title, message, type, is_read) VALUES (%s, %s, %s, %s, 0)",
            (user_id, title, message, notif_type)
        )
    except Exception as e:
        print(f"Error creating notification: {e}")
