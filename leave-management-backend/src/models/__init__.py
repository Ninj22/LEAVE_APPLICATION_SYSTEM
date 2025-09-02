from flask_sqlalchemy import SQLAlchemy

# Import models in the correct order to avoid circular dependencies
from .user import User
from .department import Department
from .leave_type import LeaveType
from .leave_balance import LeaveBalance
from .leave_application import LeaveApplication
from .login_session import LoginSession
from .password_reset_token import PasswordResetToken
from .notification import Notification

__all__ = [
    'User',
    'Department',
    'LeaveType',
    'LeaveBalance', 
    'LeaveApplication',
    'LoginSession',
    'PasswordResetToken',
    'Notification'
]

db = SQLAlchemy()

# Import all models to ensure they're loaded





