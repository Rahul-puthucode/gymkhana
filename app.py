import os
from flask import Flask, render_template, redirect, url_for, session
from config import Config
from utils.database import init_db, query_db
from routes.auth import auth_bp
from routes.member import member_bp
from routes.subscription import subscription_bp
from routes.workout import workout_bp
from routes.diet import diet_bp
from routes.progress import progress_bp
from routes.trainer import trainer_bp
from routes.gym import gym_bp
from routes.notification import notification_bp
from routes.admin import admin_bp
from routes.reports import reports_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Ensure upload directory exists
    if not os.environ.get("VERCEL"):
     os.makedirs(
        os.path.join(app.config['UPLOAD_FOLDER'], 'profiles'),
        exist_ok=True
    )
    # Initialize Database teardown context
    init_db(app)

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(member_bp)
    app.register_blueprint(subscription_bp)
    app.register_blueprint(workout_bp)
    app.register_blueprint(diet_bp)
    app.register_blueprint(progress_bp)
    app.register_blueprint(trainer_bp)
    app.register_blueprint(gym_bp)
    app.register_blueprint(notification_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(reports_bp)

    # Public Landing Page Route
    @app.route('/')
    def index():
        plans = query_db("SELECT * FROM membership_plans WHERE status = 'active' ORDER BY price ASC")
        branches = query_db("SELECT * FROM gym_branches WHERE status = 'active' ORDER BY name ASC")
        return render_template('index.html', plans=plans, branches=branches)

    # Error Handlers
    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('errors/500.html'), 500

    return app

app = create_app()

if __name__ == '__main__':
    # Run dev server on port 5000
    app.run(host='0.0.0.0', port=5000, debug=True)
