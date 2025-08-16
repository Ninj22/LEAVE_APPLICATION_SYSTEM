from flask import Flask
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_mail import Mail
from flask_migrate import Migrate

from src.extensions import db, jwt, mail, migrate
from src.routes.routes import main_bp, notifications_bp

import os
import os
from dotenv import load_dotenv
load_dotenv()

from .main import create_app


db = SQLAlchemy()
jwt = JWTManager()
mail = Mail()
migrate = Migrate()

def init_db(app):
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")

    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)

    # Register blueprints
    from src.routes.auth import auth_bp
    from src.routes.user import user_bp
    from src.routes.leave import leave_bp
    from src.routes.dashboard import dashboard_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(user_bp, url_prefix='/api/users')
    app.register_blueprint(leave_bp, url_prefix='/api/leaves')
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
    app.register_blueprint(main_bp)  # base routes
    app.register_blueprint(notifications_bp)  # notification routes

    @app.route("/")
    def index():
        return {"message": "Server is up and running Jordan!"}

    return app
