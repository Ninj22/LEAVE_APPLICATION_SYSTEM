# src/models/leave_type.py
from sqlalchemy import Column, Integer, String, Boolean, Text
from src.extensions import db
from datetime import datetime

class LeaveType(db.Model):
    __tablename__ = 'leave_types'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    max_days = db.Column(db.Integer, nullable=False)
    exclude_weekends = db.Column(db.Boolean, default=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    applications = db.relationship('LeaveApplication',foreign_keys='LeaveApplication.leave_type_id',back_populates='leave_type')
    
    balances = db.relationship('LeaveBalance',foreign_keys='LeaveBalance.leave_type_id',back_populates='leave_type')
    
    def to_dict(self):
        """Convert leave type to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'max_days': self.max_days,
            'exclude_weekends': self.exclude_weekends,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def seed_leave_types(cls):
        """Seed initial leave types"""
        leave_types = [
            {'name': 'Annual Leave', 'description': 'Annual vacation leave', 'max_days': 30, 'exclude_weekends': True},
            {'name': 'Maternity Leave', 'description': 'Leave for childbirth', 'max_days': 90, 'exclude_weekends': True},
            {'name': 'Paternity Leave', 'description': 'Leave for new fathers', 'max_days': 14, 'exclude_weekends': True},
            {'name': 'Sick Leave', 'description': 'Leave for medical reasons', 'max_days': 14, 'exclude_weekends': True},
            {'name': 'Bereavement Leave', 'description': 'Leave for bereavement', 'max_days': 4, 'exclude_weekends': True},
            {'name': 'Study Leave (Short Term)', 'description': 'Short-term study leave', 'max_days': 10, 'exclude_weekends': True},
            {'name': 'Study Leave (Long Term)', 'description': 'Long-term study leave', 'max_days': 502, 'exclude_weekends': True},
        ]
        
        for leave_type_data in leave_types:
            existing = cls.query.filter_by(name=leave_type_data['name']).first()
            if not existing:
                leave_type = cls(**leave_type_data)
                db.session.add(leave_type)
        
        try:
            db.session.commit()
            print("Leave types seeded successfully")
        except Exception as e:
            db.session.rollback()
            print(f"Error seeding leave types: {e}")
    
    @classmethod
    def get_active_types(cls):
        """Get all active leave types"""
        return cls.query.filter_by(is_active=True).all()
    
    def __repr__(self):
        return f'<LeaveType {self.name} - {self.max_days} days>'