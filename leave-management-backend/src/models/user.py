from datetime import datetime, timezone
import bcrypt
from itsdangerous import URLSafeTimedSerializer
from flask import current_app
from src.extensions import db

class User(db.Model):
       __tablename__ = 'users'
       __table_args__ = {'extend_existing': True}

       id = db.Column(db.Integer, primary_key=True)
       employee_number = db.Column(db.String(6), unique=True, nullable=False)
       email = db.Column(db.String(255), unique=True, nullable=False)
       phone_number = db.Column(db.String(20), nullable=False)
       password_hash = db.Column(db.String(255), nullable=False)
       first_name = db.Column(db.String(100), nullable=False)
       last_name = db.Column(db.String(100), nullable=False)
       role = db.Column(db.String(20), nullable=False)
       failed_login_attempts = db.Column(db.Integer, default=0)
       is_locked = db.Column(db.Boolean, default=False)
       created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
       updated_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
       is_active = db.Column(db.Boolean, default=False)
       email_verification_token = db.Column(db.String(100), nullable=True)

       #Department relationship
       department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=True)
       department_id = db.Column(
        db.Integer,
        db.ForeignKey('departments.id', use_alter=True, name="fk_users_departments"),
        nullable=True
    )

       department = db.relationship("Department", back_populates="users")

       # Relationships
       department = db.relationship('Department', foreign_keys=[department_id], back_populates='members')
       leave_applications = db.relationship('LeaveApplication', foreign_keys='LeaveApplication.applicant_id', back_populates='applicant')
       leave_balances = db.relationship('LeaveBalance', back_populates='user')
       notifications = db.relationship('Notification', back_populates='user')
       approved_applications = db.relationship('LeaveApplication', foreign_keys='LeaveApplication.approved_by')

       login_sessions = db.relationship('LoginSession', back_populates='user', lazy=True)
    #    leave_balances = db.relationship('LeaveBalance', back_populates='user', lazy=True)
       password_reset_tokens = db.relationship('PasswordResetToken', back_populates='user', lazy=True)
    #    notifications = db.relationship('Notification', back_populates='user', lazy=True)
    #    leave_applications = db.relationship('LeaveRequest', foreign_keys='LeaveRequest.employee_id', back_populates='employee', lazy=True)
       duties_assigned = db.relationship('LeaveRequest', foreign_keys='LeaveRequest.person_handling_duties_id', back_populates='duty_handler', lazy=True)
       leaves_approved = db.relationship('LeaveRequest', foreign_keys='LeaveRequest.approved_by', lazy=True)

       def set_password(self, password):
           """Hash and set password"""
           self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

       def check_password(self, password):
           return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))

       def get_role_from_employee_number(self):
           if len(self.employee_number) == 4:
               return 'staff'
           elif len(self.employee_number) == 5:
               return 'hod'
           elif len(self.employee_number) == 6:
               return 'principal_secretary'
           return 'staff'
       
       @property
       def full_name(self):
           """Get full name"""
           return f"{self.first_name} {self.last_name}"
           
   
       def to_dict(self):
           """Convert user to dictionary"""
           return {
               'id': self.id,
               'employee_number': self.employee_number,
               'email': self.email,
               'phone_number': self.phone_number,
               'first_name': self.first_name,
               'last_name': self.last_name,
               'full_name': self.full_name,
               'role': self.role,
               'is_active': self.is_active,
               'is_locked': self.is_locked,
               'department_id': self.department_id,
               'department_name': self.department.name if self.department else None,
               'created_at': self.created_at.isoformat() if self.created_at else None,
               'updated_at': self.updated_at.isoformat() if self.updated_at else None,
               'failed_login_attempts': self.failed_login_attempts,
               'email_verification_token': self.email_verification_token
           }
       
       def __repr__(self):
        return f'<User {self.employee_number} - {self.full_name}>'

       def generate_verification_token(self):
           s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
           return s.dumps(self.email, salt='email-verify')

       def verify_token(self, token, max_age=3600):
           s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
           try:
               email = s.loads(token, salt='email-verify', max_age=max_age)
           except Exception:
               return False
           return self.email == email

       def generate_password_reset_token(self):
           s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
           return s.dumps(self.email, salt='password-reset')
       
       def init_leave_balances(self):
        """Initialize leave balances for new user"""
        from src.models.leave_type import LeaveType
        from src.models.leave_balance import LeaveBalance
        
        current_year = datetime.now().year
        
        # Define default leave allocations based on requirements
        leave_allocations = {
            'Annual Leave': 30,
            'Sick Leave': 14,
            'Maternity Leave': 90,
            'Paternity Leave': 14,
            'Bereavement Leave': 4,
            'Study Leave (Short Term)': 10,
            'Study Leave (Long Term)': 502
        }
        
        for leave_type_name, days in leave_allocations.items():
            leave_type = LeaveType.query.filter_by(name=leave_type_name).first()
            if leave_type:
                # Check if balance already exists
                existing_balance = LeaveBalance.query.filter_by(
                    user_id=self.id,
                    leave_type_id=leave_type.id,
                    year=current_year
                ).first()
                
                if not existing_balance:
                    balance = LeaveBalance(
                        user_id=self.id,
                        leave_type_id=leave_type.id,
                        total_days=days,
                        used_days=0,
                        balance=days,
                        year=current_year
                    )
                    db.session.add(balance)