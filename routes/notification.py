from flask import Blueprint, render_template, redirect, url_for, flash, session, jsonify
from utils.database import query_db, execute_db
from utils.auth import login_required

notification_bp = Blueprint('notification', __name__, url_prefix='/notifications')

@notification_bp.route('/')
@login_required
def index():
    user_id = session.get('user_id')
    notifications = query_db(
        "SELECT * FROM notifications WHERE user_id = %s ORDER BY created_at DESC",
        (user_id,)
    )
    return render_template('member/notifications.html', notifications=notifications)

@notification_bp.route('/api/unread-count')
@login_required
def unread_count():
    user_id = session.get('user_id')
    res = query_db(
        "SELECT COUNT(*) as count FROM notifications WHERE user_id = %s AND is_read = 0",
        (user_id,), one=True
    )
    return jsonify({'count': res['count'] if res else 0})

@notification_bp.route('/mark-read/<int:notif_id>', methods=['POST'])
@login_required
def mark_read(notif_id):
    user_id = session.get('user_id')
    execute_db("UPDATE notifications SET is_read = 1 WHERE id = %s AND user_id = %s", (notif_id, user_id))
    return redirect(url_for('notification.index'))

@notification_bp.route('/mark-all-read', methods=['POST'])
@login_required
def mark_all_read():
    user_id = session.get('user_id')
    execute_db("UPDATE notifications SET is_read = 1 WHERE user_id = %s", (user_id,))
    flash('All notifications marked as read.', 'info')
    return redirect(url_for('notification.index'))
