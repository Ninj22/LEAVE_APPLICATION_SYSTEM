import os
from datetime import timedelta, datetime, timezone
from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_mail import Mail
from dotenv import load_dotenv
from flask_migrate import Migrate
from src.extensions import db, migrate
from src.routes.auth import auth_bp
from src.routes.leave import leave_bp
from src.routes.user import user_bp
from src.routes.dashboard import dashboard_bp
from src.routes.routes import notifications_bp
from src.routes.routes import main_bp
from src.models.user import User
from src.models.leave_balance import LeaveBalance
from src.models.leave_type import LeaveType
from src.models.department import Department
from src.models.login_session import LoginSession
from src.models.password_reset_token import PasswordResetToken
from src.routes.leave_balance import leave_balance_bp

load_dotenv()

def create_app():
    app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))

    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'asdf#FGSgvasgf$5$WGT')
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'jwt-secret-string')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///app.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

    CORS(app, origins=["http://localhost:3000"], supports_credentials=True)

    db.init_app(app)
    migrate.init_app(app, db)
    migrate = Migrate(app, db)
    jwt = JWTManager(app)
    mail = Mail(app)

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(leave_bp, url_prefix="/api/leave")
    app.register_blueprint(user_bp, url_prefix="/api/users")
    app.register_blueprint(dashboard_bp, url_prefix="/api/dashboard")
    app.register_blueprint(notifications_bp, url_prefix="/api/notifications")
    app.register_blueprint(main_bp)
    app.register_blueprint(leave_balance_bp, url_prefix="/api/leave_balances")

    with app.app_context():
        db.drop_all()
        db.create_all()
        # Seed LeaveType data
        leave_types = [
            {'name': 'Annual Leave', 'max_days': 30, 'exclude_weekends': True},
            {'name': 'Maternity Leave', 'max_days': 90, 'exclude_weekends': True},
            {'name': 'Paternity Leave', 'max_days': 14, 'exclude_weekends': True},
            {'name': 'Sick Leave', 'max_days': 14, 'exclude_weekends': True},
            {'name': 'Bereavement Leave', 'max_days': 4, 'exclude_weekends': True},
            {'name': 'Study Leave (Short Term)', 'max_days': 10, 'exclude_weekends': True},
            {'name': 'Study Leave (Long Term)', 'max_days': 502, 'exclude_weekends': True},
        ]
        for leave_type_data in leave_types:
            existing = LeaveType.query.filter_by(name=leave_type_data['name']).first()
            if not existing:
                leave_type = LeaveType(**leave_type_data)
                db.session.add(leave_type)
        db.session.commit()

    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve(path):
        static_folder_path = app.static_folder
        if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
            return send_from_directory(static_folder_path, path)
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        return "Index file not found", 404

    @leave_bp.route('/leave_balances', methods=['GET'])
    def get_leave_balances():
        leave_balances = LeaveBalance.query.all()
        return jsonify([lb.to_dict() for lb in leave_balances])

    return app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)