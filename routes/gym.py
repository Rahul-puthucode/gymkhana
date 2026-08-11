from flask import Blueprint, render_template, jsonify
from utils.database import query_db

gym_bp = Blueprint('gym', __name__, url_prefix='/gym')

@gym_bp.route('/locations')
def locations():
    branches = query_db("SELECT * FROM gym_branches WHERE status = 'active' ORDER BY name ASC")
    return render_template('member/gym_locations.html', branches=branches)

@gym_bp.route('/api/branches')
def api_branches():
    branches = query_db("SELECT * FROM gym_branches WHERE status = 'active' ORDER BY name ASC")
    return jsonify(branches)
