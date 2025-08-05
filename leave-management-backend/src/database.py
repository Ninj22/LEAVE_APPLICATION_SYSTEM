from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from src.routes.auth import auth_bp
from src.routes.user import user_bp
from src.routes.leave import leave_bp
from src.routes.dashboard import dashboard_bp

db = SQLAlchemy()
def init_db(app):
    db.init_app(app)

migrate = Migrate()

def create_app():
    app = Flask(__name__)
    db.init_app(app)
    migrate.init_app(app, db)

    # Register your blueprints here
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(user_bp, url_prefix='/api/users')
    app.register_blueprint(leave_bp, url_prefix='/api/leaves')
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')

    return app
