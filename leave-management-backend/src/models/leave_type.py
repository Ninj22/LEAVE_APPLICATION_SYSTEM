from sqlalchemy import Column, Integer, String
from src.extensions import db

class LeaveType(db.Model):
    __tablename__ = 'leave_types'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(String(255), nullable=True)

    def __repr__(self):
        return f"<LeaveType(id={self.id}, name='{self.name}')>"
