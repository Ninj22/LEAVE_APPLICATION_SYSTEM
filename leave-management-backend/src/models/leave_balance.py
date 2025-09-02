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
    balance = db.Column(db.Float, default=0.0, nullable=False)
    used = db.Column(db.Float, default=0.0, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    total_days = db.Column(db.Integer, default=30)   # <-- add this if needed

    # Relationships
    user = db.relationship('User', back_populates='leave_balances')
    leave_type = db.relationship('LeaveType', back_populates='balances')
    
    # Unique constraint to prevent duplicate balances for same user/leave_type/year
    __table_args__ = (
        db.UniqueConstraint('user_id', 'leave_type_id', 'year', name='_user_leave_type_year_uc'),
    )
    
    @property
    def available(self):
        """Calculate available leave balance"""
        return max(0, self.balance - self.used)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'leave_type_id': self.leave_type_id,
            'leave_type_name': self.leave_type.name if self.leave_type else None,
            'balance': self.balance,
            'used': self.used,
            'available': self.available,
            'year': self.year,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<LeaveBalance {self.user_id}:{self.leave_type_id} - {self.available}/{self.balance}>'