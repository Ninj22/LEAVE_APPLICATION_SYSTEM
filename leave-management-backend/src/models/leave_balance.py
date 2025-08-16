# src/models/leave_balance.py
from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from src.extensions import db
from datetime import datetime

class LeaveBalance(db.Model):
    __tablename__ = 'leave_balances'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    leave_type_id = db.Column(db.Integer, db.ForeignKey('leave_types.id'), nullable=False)
    year = db.Column(db.Integer, nullable=False, default=lambda: datetime.now().year)
    
    # Leave allocation and usage
    total_days = db.Column(db.Float, nullable=False, default=0)  # Total allocated for the year
    used_days = db.Column(db.Float, nullable=False, default=0)   # Days used
    balance = db.Column(db.Float, nullable=False, default=0)     # Remaining days (computed)
    
    # Relationships
    user = db.relationship("User", back_populates="leave_balances")
    leave_type = db.relationship("LeaveType", back_populates="balances")
    
    def remaining_days(self):
        """Calculate remaining leave days"""
        return self.total_days - self.used_days
    
    def update_balance(self):
        """Update balance based on total and used days"""
        self.balance = self.total_days - self.used_days
        return self.balance
    
    def can_take_leave(self, days_requested):
        """Check if user can take requested days"""
        return self.remaining_days() >= days_requested
    
    def use_leave_days(self, days):
        """Deduct leave days from balance"""
        if self.can_take_leave(days):
            self.used_days += days
            self.update_balance()
            return True
        return False
    
    def restore_leave_days(self, days):
        """Restore leave days to balance (e.g., when leave is cancelled)"""
        self.used_days = max(0, self.used_days - days)
        self.update_balance()
    
    def to_dict(self):
        """Convert leave balance to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_name': self.user.full_name if self.user else None,
            'leave_type_id': self.leave_type_id,
            'leave_type_name': self.leave_type.name if self.leave_type else None,
            'year': self.year,
            'total_days': self.total_days,
            'used_days': self.used_days,
            'balance': self.balance,
            'remaining_days': self.remaining_days()
        }
    
    @classmethod
    def get_user_balance(cls, user_id, leave_type_id, year=None):
        """Get user's balance for specific leave type and year"""
        if year is None:
            year = datetime.now().year
        return cls.query.filter_by(
            user_id=user_id,
            leave_type_id=leave_type_id,
            year=year
        ).first()
    
    @classmethod
    def get_user_all_balances(cls, user_id, year=None):
        """Get all leave balances for a user in a specific year"""
        if year is None:
            year = datetime.now().year
        return cls.query.filter_by(user_id=user_id, year=year).all()
    
    def __repr__(self):
        return f'<LeaveBalance {self.user.full_name if self.user else "Unknown"} - {self.leave_type.name if self.leave_type else "Unknown"} - {self.year}: {self.remaining_days()}/{self.total_days}>'