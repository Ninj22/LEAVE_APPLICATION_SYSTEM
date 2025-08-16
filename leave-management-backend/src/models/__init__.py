from flask_sqlalchemy import SQLAlchemy
from .leave import LeaveType, LeaveRequest, LeaveBalance
from .user import User
from .department import Department
from .login_session import LoginSession
from .password_reset_token import PasswordResetToken
from .notification import Notification

__all__ = [
    'LeaveType',
    'LeaveRequest',
    'LeaveBalance',
    'User',
    'Department',
    'LoginSession',
    'PasswordResetToken',
    'Notification'
]

db = SQLAlchemy()

# Import all models to ensure they're loaded

    



