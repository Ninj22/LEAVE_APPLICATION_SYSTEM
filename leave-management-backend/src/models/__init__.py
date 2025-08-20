from flask_sqlalchemy import SQLAlchemy
from .user import User
from .leave_type import LeaveType
from .leave_balance import LeaveBalance
from .leave_application import LeaveApplication
from .department import Department
from .login_session import LoginSession
from .password_reset_token import PasswordResetToken
from .notification import Notification

__all__ = [
    'LeaveType',
    'LeaveRequest',
    'LeaveBalance',
    'LeaveApplication',
    'User',
    'Department',
    'LoginSession',
    'PasswordResetToken',
    'Notification'
]

db = SQLAlchemy()

# Import all models to ensure they're loaded

    



