from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from utils.database import query_db, execute_db
from utils.auth import login_required, role_required
from utils.helpers import calculate_remaining_days, log_activity, send_notification

subscription_bp = Blueprint('subscription', __name__, url_prefix='/subscription')

@subscription_bp.route('/plans')
def plans():
    active_plans = query_db("SELECT * FROM membership_plans WHERE status = 'active' ORDER BY price ASC")
    return render_template('member/membership_plans.html', plans=active_plans)

@subscription_bp.route('/my-membership')
@login_required
@role_required('MEMBER')
def my_membership():
    member_id = session.get('user_id')
    
    # Fetch active or latest subscription
    subscription = query_db(
        """SELECT s.*, p.name as plan_name, p.description as plan_description, p.duration_months, p.benefits
           FROM subscriptions s
           JOIN membership_plans p ON s.plan_id = p.id
           WHERE s.member_id = %s
           ORDER BY s.id DESC LIMIT 1""",
        (member_id,), one=True
    )
    
    status_label = "No Active Subscription"
    remaining_days = 0
    
    if subscription:
        remaining_days = calculate_remaining_days(subscription['expiry_date'])
        
        if remaining_days <= 0:
            status_label = "Expired"
            if subscription['status'] != 'expired':
                execute_db("UPDATE subscriptions SET status = 'expired' WHERE id = %s", (subscription['id'],))
                subscription['status'] = 'expired'
        elif remaining_days <= 7:
            status_label = "Expiring Soon"
        else:
            status_label = "Active"

    # Fetch available plans for subscribe / upgrade / renewal
    available_plans = query_db("SELECT * FROM membership_plans WHERE status = 'active' ORDER BY price ASC")
    
    # Fetch subscription history
    history = query_db(
        """SELECT sh.*, p.name as plan_name
           FROM subscription_history sh
           JOIN membership_plans p ON sh.plan_id = p.id
           WHERE sh.member_id = %s
           ORDER BY sh.date DESC""",
        (member_id,)
    )

    return render_template(
        'member/membership.html', 
        subscription=subscription, 
        remaining_days=remaining_days,
        status_label=status_label,
        available_plans=available_plans,
        history=history
    )

@subscription_bp.route('/subscribe', methods=['POST'])
@login_required
@role_required('MEMBER')
def subscribe():
    member_id = session.get('user_id')
    plan_id = request.form.get('plan_id', type=int)

    if not plan_id:
        flash('Invalid plan selected.', 'danger')
        return redirect(url_for('subscription.my_membership'))

    plan = query_db("SELECT * FROM membership_plans WHERE id = %s AND status = 'active'", (plan_id,), one=True)
    if not plan:
        flash('Selected membership plan is no longer available.', 'danger')
        return redirect(url_for('subscription.my_membership'))

    start_d = date.today()
    expiry_d = start_d + relativedelta(months=plan['duration_months'])

    # Deactivate existing active subscriptions
    execute_db("UPDATE subscriptions SET status = 'expired' WHERE member_id = %s AND status = 'active'", (member_id,))

    # Insert new subscription
    sub_id = execute_db(
        """INSERT INTO subscriptions (member_id, plan_id, start_date, expiry_date, amount, status)
           VALUES (%s, %s, %s, %s, %s, 'active')""",
        (member_id, plan['id'], start_d, expiry_d, plan['price'])
    )

    # Insert history log
    execute_db(
        """INSERT INTO subscription_history (subscription_id, member_id, plan_id, action, amount)
           VALUES (%s, %s, %s, 'SUBSCRIBE', %s)""",
        (sub_id, member_id, plan['id'], plan['price'])
    )

    log_activity(member_id, 'MEMBER', 'SUBSCRIPTION_CREATED', f"Subscribed to {plan['name']} (₹{plan['price']})")
    send_notification(
        member_id, 
        "Subscription Activated!", 
        f"You are now subscribed to the {plan['name']} plan until {expiry_d.strftime('%b %d, %Y')}.",
        "success"
    )

    flash(f"Successfully subscribed to {plan['name']}! Valid until {expiry_d.strftime('%b %d, %Y')}.", 'success')
    return redirect(url_for('subscription.my_membership'))
