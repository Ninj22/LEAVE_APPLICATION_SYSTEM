# src/models/__init__.py
from flask_sqlalchemy import SQLAlchemy
from .user import User
from .leave_balance import LeaveBalance
from .leave_type import LeaveType
from .leave_application import LeaveApplication
from .login_session import LoginSession
from .password_reset_token import PasswordResetToken
from .department import Department


db = SQLAlchemy()

# Import all models to ensure they're loaded

    



