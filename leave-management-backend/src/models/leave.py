from datetime import datetime
from sqlalchemy.orm import relationship
from src.extensions import db

class LeaveType(db.Model):
    __tablename__ = 'leave_types'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    description = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    max_days = db.Column(db.Integer, nullable=False)
    exclude_weekends = db.Column(db.Boolean, default=True)

    # Relationship
    leave_requests = relationship('LeaveRequest', back_populates='leave_type')

    def __repr__(self):
        return f"<LeaveType {self.name}>"

class LeaveRequest(db.Model):
    __tablename__ = 'leave_requests'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    leave_type_id = db.Column(db.Integer, db.ForeignKey('leave_types.id'), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    reason = db.Column(db.String(255))
    status = db.Column(db.String(20), default='Pending')
    applied_on = db.Column(db.DateTime, default=datetime.utcnow)
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    approval_date = db.Column(db.DateTime, nullable=True)
    person_handling_duties_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    hod_approved = db.Column(db.Boolean, default=False)
    hod_approval_date = db.Column(db.DateTime)
    hod_comments = db.Column(db.String(255))
    principal_secretary_approved = db.Column(db.Boolean, default=False)
    principal_secretary_approval_date = db.Column(db.DateTime)
    principal_secretary_comments = db.Column(db.String(255))

    # Relationships
    leave_type = relationship('LeaveType', back_populates='leave_requests')
    employee = relationship('User', back_populates='leave_applications', foreign_keys=[employee_id])
    approver = relationship('User', back_populates='leaves_approved', foreign_keys=[approved_by])
    duty_handler = relationship('User', back_populates='duties_assigned', foreign_keys=[person_handling_duties_id])

    def to_dict(self):
        return {
            'id': self.id,
            'employee_id': self.employee_id,
            'leave_type_id': self.leave_type_id,
            'leave_type': self.leave_type.name if self.leave_type else None,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'reason': self.reason,
            'status': self.status,
            'applied_on': self.applied_on.isoformat() if self.applied_on else None,
            'approved_by': self.approved_by,
            'approval_date': self.approval_date.isoformat() if self.approval_date else None,
            'person_handling_duties_id': self.person_handling_duties_id
        }

    def __repr__(self):
        return f"<LeaveRequest {self.id} - {self.status}>"

class LeaveBalance(db.Model):
    __tablename__ = 'leave_balances'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    leave_type_id = db.Column(db.Integer, db.ForeignKey('leave_types.id'), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    balance = db.Column(db.Integer, nullable=False, default=0)

    # Relationships
    user = relationship('User', back_populates='leave_balances')
    leave_type = relationship('LeaveType')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'leave_type_id': self.leave_type_id,
            'leave_type': self.leave_type.name if self.leave_type else None,
            'year': self.year,
            'balance': self.balance
        }

    def __repr__(self):
        return f"<LeaveBalance {self.user_id} - {self.leave_type_id} - {self.year}>"