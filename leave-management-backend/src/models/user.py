# src/models/user.py
from datetime import datetime, timezone
import bcrypt
from itsdangerous import URLSafeTimedSerializer
from flask import current_app
from src.extensions import db
from src.models.login_session import LoginSession

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    employee_number = db.Column(db.String(6), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'staff', 'hod', 'principal_secretary'
    failed_login_attempts = db.Column(db.Integer, default=0)
    is_locked = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    is_active = db.Column(db.Boolean, default=False)
    email_verification_token = db.Column(db.String(100), nullable=True)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id', use_alter=True), nullable=True)
    hod_id = db.Column(db.Integer, db.ForeignKey('departments.id', use_alter=True), nullable=True)  # If exists

    department = db.relationship('Department', back_populates='users', foreign_keys=[department_id])
    login_sessions = db.relationship("LoginSession", backref="user", lazy=True)
    leave_applications = db.relationship("LeaveApplication", backref="applicant", lazy=True)
    duties_assigned = db.relationship("LeaveApplication", foreign_keys="LeaveApplication.person_handling_duties_id", backref="duty_handler", lazy=True)
    leaves_approved = db.relationship("LeaveApplication", foreign_keys="LeaveApplication.approved_by", backref="approver", lazy=True)
    leave_balances = db.relationship("LeaveBalance", back_populates="user", lazy=True)
    password_reset_tokens = db.relationship("PasswordResetToken", backref="user", lazy=True)

    def set_password(self, password):
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

    def to_dict(self):
        return {
            'id': self.id,
            'employee_number': self.employee_number,
            'email': self.email,
            'phone_number': self.phone_number,
            'first_name': self.first_name,
            'last_name': self.last_name,
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
        return f'<User {self.employee_number}>'

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
    