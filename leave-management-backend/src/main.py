import os
from datetime import timedelta
from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_mail import Mail
from dotenv import load_dotenv
from src.extensions import db, jwt, migrate
from src.routes.auth import auth_bp
from src.routes.leave import leave_bp
from src.routes.user import user_bp
from src.routes.dashboard import dashboard_bp
from src.routes.routes import notifications_bp, main_bp
from src.routes.leave_balance import leave_balance_bp
from src.routes.department import department_bp

load_dotenv()

def create_app():
    app = Flask(__name__)

    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'asdf#FGSgvasgf$5$WGT')
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'jwt-secret-string')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///app.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['DEVELOPMENT'] = os.environ.get('FLASK_ENV') == 'development'

    # Email configuration
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

    CORS(app, origins=["http://localhost:3000"], supports_credentials=True)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    JWTManager(app)
    mail = Mail(app)

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(leave_bp, url_prefix="/api/leave")
    app.register_blueprint(user_bp, url_prefix="/api/users")
    app.register_blueprint(dashboard_bp, url_prefix="/api/dashboard")
    app.register_blueprint(department_bp, url_prefix='/api/department')
    app.register_blueprint(notifications_bp, url_prefix="/api/notifications")
    app.register_blueprint(main_bp)
    app.register_blueprint(leave_balance_bp, url_prefix="/api/leave_balances")
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Not found'}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return {'error': 'Internal server error'}, 500
    
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return {'error': 'Token has expired'}, 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return {'error': 'Invalid token'}, 401
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return {'error': 'Authentication required'}, 401
    
    # Health check endpoint
    @app.route('/api/health')
    def health_check():
        return {'status': 'healthy', 'message': 'Leave Management System is running'}, 200
    
    # Initialize database and seed data
    with app.app_context():
        # Import models here to avoid circular imports
        from src.models import User, Department, LeaveType
        
        # Configure mappers first
        db.configure_mappers()
        
        # Create tables
        db.create_all()
        
        # Seed initial data
        seed_initial_data()
    
    return app

def seed_initial_data():
    """Seed initial data for the application"""
    try:
        # Import models here to avoid circular imports
        from src.models.leave_type import LeaveType
        from src.models.user import User
        
        # Seed leave types
        leave_types_data = [
            {'name': 'Annual Leave', 'description': 'Annual vacation leave', 'max_days': 30, 'exclude_weekends': True},
            {'name': 'Maternity Leave', 'description': 'Leave for childbirth', 'max_days': 90, 'exclude_weekends': True},
            {'name': 'Paternity Leave', 'description': 'Leave for new fathers', 'max_days': 14, 'exclude_weekends': True},
            {'name': 'Sick Leave', 'description': 'Leave for medical reasons', 'max_days': 14, 'exclude_weekends': True},
            {'name': 'Bereavement Leave', 'description': 'Leave for bereavement', 'max_days': 4, 'exclude_weekends': True},
            {'name': 'Study Leave (Short Term)', 'description': 'Short-term study leave', 'max_days': 10, 'exclude_weekends': True},
            {'name': 'Study Leave (Long Term)', 'description': 'Long-term study leave', 'max_days': 502, 'exclude_weekends': True},
        ]
        
        for leave_type_data in leave_types_data:
            existing = LeaveType.query.filter_by(name=leave_type_data['name']).first()
            if not existing:
                leave_type = LeaveType(**leave_type_data)
                db.session.add(leave_type)
        
        # Create superuser if doesn't exist
        existing_admin = User.query.filter_by(email='admin@ict.go.ke').first()
        superuser_created = False
        
        if not existing_admin:
            superuser = User(
                employee_number='000001',
                email='admin@ict.go.ke',
                phone_number='+254706356836',
                first_name='System',
                last_name='Administrator',
                role='principal_secretary', # Super Admin role number
                is_active=True
            )
            superuser.set_password('admin123')  # Change this in production
            db.session.add(superuser)
            superuser_created = True
        
        # Commit all changes
        db.session.commit()
        
        # Initialize leave balances for superuser if created
        if superuser_created:
            superuser.init_leave_balances()
            db.session.commit()
            print("Superuser created successfully")
            print("Email: admin@ict.go.ke")
            print("Employee Number: 000001")
            print("Password: admin123")
            print("Please change the password after first login!")
        
        print("Initial data seeded successfully")
        
    except Exception as e:
        db.session.rollback()
        print(f"Error seeding initial data: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)