import csv
import io
from flask import Blueprint, render_template, request, Response, session
from utils.database import query_db
from utils.auth import login_required, role_required

reports_bp = Blueprint('reports', __name__, url_prefix='/admin/reports')

@reports_bp.route('/')
@login_required
@role_required('ADMIN')
def index():
    status_filter = request.args.get('status', '').strip()
    
    # 1. Subscriptions report query
    sub_query = """SELECT s.*, u.name as member_name, u.email, p.name as plan_name
                   FROM subscriptions s
                   JOIN users u ON s.member_id = u.id
                   JOIN membership_plans p ON s.plan_id = p.id
                   WHERE 1=1"""
    params = []
    if status_filter:
        sub_query += " AND s.status = %s"
        params.append(status_filter)
    sub_query += " ORDER BY s.id DESC"
    
    subscriptions_report = query_db(sub_query, tuple(params))
    
    # Revenue summary
    total_rev_res = query_db("SELECT SUM(amount) as total FROM subscriptions", one=True)
    total_revenue = float(total_rev_res['total']) if total_rev_res and total_rev_res['total'] else 0.0

    # User breakdown summary
    total_members = query_db("SELECT COUNT(*) as cnt FROM users u JOIN roles r ON u.role_id = r.id WHERE LOWER(r.name) = 'member'", one=True)['cnt']
    active_users = query_db("SELECT COUNT(*) as cnt FROM users WHERE status = 'active'", one=True)['cnt']

    # Fitness averages
    fit_summary = query_db("SELECT AVG(weight) as avg_weight, AVG(bmi) as avg_bmi FROM fitness_progress", one=True)
    avg_weight = round(float(fit_summary['avg_weight']), 1) if fit_summary and fit_summary['avg_weight'] else 0.0
    avg_bmi = round(float(fit_summary['avg_bmi']), 1) if fit_summary and fit_summary['avg_bmi'] else 0.0

    return render_template(
        'admin/reports.html',
        subscriptions_report=subscriptions_report,
        status_filter=status_filter,
        total_revenue=total_revenue,
        total_members=total_members,
        active_users=active_users,
        avg_weight=avg_weight,
        avg_bmi=avg_bmi
    )

@reports_bp.route('/export-csv')
@login_required
@role_required('ADMIN')
def export_csv():
    report_type = request.args.get('type', 'subscriptions')
    
    output = io.StringIO()
    writer = csv.writer(output)

    if report_type == 'users':
        writer.writerow(['ID', 'Name', 'Email', 'Role', 'Phone', 'Gender', 'Status', 'Created At'])
        rows = query_db(
            """SELECT u.id, u.name, u.email, r.name as role, u.phone, u.gender, u.status, u.created_at
               FROM users u JOIN roles r ON u.role_id = r.id ORDER BY u.id ASC"""
        )
        for r in rows:
            writer.writerow([r['id'], r['name'], r['email'], r['role'], r['phone'], r['gender'], r['status'], r['created_at']])
        filename = "gymkhana_users_report.csv"
        
    elif report_type == 'fitness':
        writer.writerow(['Record ID', 'Member ID', 'Member Name', 'Weight (kg)', 'Height (cm)', 'BMI', 'Recorded Date'])
        rows = query_db(
            """SELECT fp.id, fp.member_id, u.name, fp.weight, fp.height, fp.bmi, fp.recorded_at
               FROM fitness_progress fp JOIN users u ON fp.member_id = u.id ORDER BY fp.recorded_at DESC"""
        )
        for r in rows:
            writer.writerow([r['id'], r['member_id'], r['name'], r['weight'], r['height'], r['bmi'], r['recorded_at']])
        filename = "gymkhana_fitness_report.csv"
        
    else: # subscriptions
        writer.writerow(['Subscription ID', 'Member Name', 'Email', 'Plan Name', 'Amount (INR)', 'Start Date', 'Expiry Date', 'Status'])
        rows = query_db(
            """SELECT s.id, u.name, u.email, p.name as plan_name, s.amount, s.start_date, s.expiry_date, s.status
               FROM subscriptions s JOIN users u ON s.member_id = u.id JOIN membership_plans p ON s.plan_id = p.id ORDER BY s.id DESC"""
        )
        for r in rows:
            writer.writerow([r['id'], r['name'], r['email'], r['plan_name'], r['amount'], r['start_date'], r['expiry_date'], r['status']])
        filename = "gymkhana_subscriptions_report.csv"

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )
