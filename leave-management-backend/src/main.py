import os
from datetime import timedelta
from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_mail import Mail
from dotenv import load_dotenv
from src.extensions import db, migrate
from src.routes.auth import auth_bp
from src.routes.leave import leave_bp
from src.routes.user import user_bp
from src.routes.dashboard import dashboard_bp
from src.routes.routes import notifications_bp, main_bp
from src.routes.leave_balance import leave_balance_bp
from src.models.leave import LeaveType

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

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    JWTManager(app)
    mail = Mail(app)
    CORS(app)

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(leave_bp, url_prefix="/api/leave")
    app.register_blueprint(user_bp, url_prefix="/api/users")
    app.register_blueprint(dashboard_bp, url_prefix="/api/dashboard")
    app.register_blueprint(notifications_bp, url_prefix="/api/notifications")
    app.register_blueprint(main_bp)
    app.register_blueprint(leave_balance_bp, url_prefix="/api/leave_balances")

    with app.app_context():
        db.configure_mappers()
    
        # leave_types = [
        #     {'name': 'Annual Leave', 'description': 'Annual vacation leave', 'max_days': 30, 'exclude_weekends': True},
        #     {'name': 'Maternity Leave', 'description': 'Leave for childbirth', 'max_days': 90, 'exclude_weekends': True},
        #     {'name': 'Paternity Leave', 'description': 'Leave for new fathers', 'max_days': 14, 'exclude_weekends': True},
        #     {'name': 'Sick Leave', 'description': 'Leave for medical reasons', 'max_days': 14, 'exclude_weekends': True},
        #     {'name': 'Bereavement Leave', 'description': 'Leave for bereavement', 'max_days': 4, 'exclude_weekends': True},
        #     {'name': 'Study Leave (Short Term)', 'description': 'Short-term study leave', 'max_days': 10, 'exclude_weekends': True},
        #     {'name': 'Study Leave (Long Term)', 'description': 'Long-term study leave', 'max_days': 502, 'exclude_weekends': True},
        # ]
        # for leave_type_data in leave_types:
        #     existing = LeaveType.query.filter_by(name=leave_type_data['name']).first()
        #     if not existing:
        #         leave_type = LeaveType(**leave_type_data)
        #         db.session.add(leave_type)
        # db.session.commit()

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

    return app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
    
# import os
# from datetime import timedelta
# from flask import Flask, send_from_directory
# from flask_cors import CORS
# from flask_jwt_extended import JWTManager
# from flask_mail import Mail
# from dotenv import load_dotenv
# from src.extensions import db, migrate
# from src.routes.auth import auth_bp
# from src.routes.leave import leave_bp
# from src.routes.user import user_bp
# from src.routes.dashboard import dashboard_bp
# from src.routes.routes import notifications_bp, main_bp
# from src.routes.leave_balance import leave_balance_bp
# from src.models.leave import LeaveType

# load_dotenv()

# def create_app():
#     app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
#     app.config.from_object('config.Config')

#     app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'asdf#FGSgvasgf$5$WGT')
#     app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'jwt-secret-string')
#     app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
#     app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///app.db')
#     app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
#     app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
#     app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
#     app.config['MAIL_USE_TLS'] = True
#     app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
#     app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
#     app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

#     CORS(app, origins=["http://localhost:3000"], supports_credentials=True)

#     # Initialize extensions
#     db.init_app(app)
#     migrate.init_app(app, db)
#     JWTManager(app)
#     Mail(app)
#     CORS(app)
    


#     # Register blueprints
#     app.register_blueprint(auth_bp, url_prefix="/api/auth")
#     app.register_blueprint(leave_bp, url_prefix="/api/leave")
#     app.register_blueprint(user_bp, url_prefix="/api/users")
#     app.register_blueprint(dashboard_bp, url_prefix="/api/dashboard")
#     app.register_blueprint(notifications_bp, url_prefix="/api/notifications")
#     app.register_blueprint(main_bp)
#     app.register_blueprint(leave_balance_bp, url_prefix="/api/leave_balances")

#     with app.app_context():
#         db.create_all()
#         # Seed LeaveType data
#         leave_types = [
#             {'name': 'Annual Leave', 'description': 'Annual vacation leave', 'max_days': 30, 'exclude_weekends': True},
#             {'name': 'Maternity Leave', 'description': 'Leave for childbirth', 'max_days': 90, 'exclude_weekends': True},
#             {'name': 'Paternity Leave', 'description': 'Leave for new fathers', 'max_days': 14, 'exclude_weekends': True},
#             {'name': 'Sick Leave', 'description': 'Leave for medical reasons', 'max_days': 14, 'exclude_weekends': True},
#             {'name': 'Bereavement Leave', 'description': 'Leave for bereavement', 'max_days': 4, 'exclude_weekends': True},
#             {'name': 'Study Leave (Short Term)', 'description': 'Short-term study leave', 'max_days': 10, 'exclude_weekends': True},
#             {'name': 'Study Leave (Long Term)', 'description': 'Long-term study leave', 'max_days': 502, 'exclude_weekends': True},
#         ]
#         for leave_type_data in leave_types:
#             existing = LeaveType.query.filter_by(name=leave_type_data['name']).first()
#             if not existing:
#                 leave_type = LeaveType(**leave_type_data)
#                 db.session.add(leave_type)
#         db.session.commit()

#     @app.route('/', defaults={'path': ''})
#     @app.route('/<path:path>')
#     def serve(path):
#         static_folder_path = app.static_folder
#         if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
#             return send_from_directory(static_folder_path, path)
#         index_path = os.path.join(static_folder_path, 'index.html')
#         if os.path.exists(index_path):
#             return send_from_directory(static_folder_path, 'index.html')
#         return "Index file not found", 404

#     return app

# app = create_app()

# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=5000, debug=True)