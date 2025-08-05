from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from src.extensions import db

class LeaveBalance(db.Model):
    __tablename__ = 'leave_balances'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    leave_type_id = db.Column(db.Integer, db.ForeignKey('leave_types.id'), nullable=False)
    balance = db.Column(db.Integer, nullable=False)
    total_days = Column(Float, nullable=False, default=0)
    used_days = Column(Float, nullable=False, default=0)

    # Relationship (optional)
    user = relationship("User", back_populates="leave_balances")

    def remaining_days(self):
        return self.total_days - self.used_days