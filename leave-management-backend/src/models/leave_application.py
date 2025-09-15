# src/models/leave_application.py
from datetime import datetime, timezone
from src.extensions import db

class LeaveApplication(db.Model):
    __tablename__ = 'leave_applications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    leave_type_id = db.Column(db.Integer, db.ForeignKey('leave_types.id'), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    days_requested = db.Column(db.Float, nullable=False)
    reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='pending', nullable=False)
    comments = db.Column(db.Text, nullable=True)
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    
    # Adding missing fields that might be referenced
    person_handling_duties = db.Column(db.String(255), nullable=True)  # Name of person handling duties
    person_handling_duties_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # FK to User
    handover_notes = db.Column(db.Text, nullable=True)  # Notes for handover
    attachment_path = db.Column(db.String(500), nullable=True)  # Path to any attachments
    
    # Relationships - NO back_populates to avoid circular issues
    user = db.relationship('User',foreign_keys=[user_id],back_populates='leave_applications')
    
    leave_type = db.relationship('LeaveType',foreign_keys=[leave_type_id],back_populates='applications')
    
    approver = db.relationship('User', foreign_keys=[approved_by])
    person_handling = db.relationship('User', foreign_keys=[person_handling_duties_id])
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_name': f"{self.user.first_name} {self.user.last_name}" if self.user else None,
            'user_employee_number': self.user.employee_number if self.user else None,
            'leave_type_id': self.leave_type_id,
            'leave_type_name': self.leave_type.name if self.leave_type else None,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'days_requested': self.days_requested,
            'reason': self.reason,
            'status': self.status,
            'comments': self.comments,
            'approved_by': self.approved_by,
            'approver_name': f"{self.approver.first_name} {self.approver.last_name}" if self.approver else None,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'person_handling_duties': self.person_handling_duties,
            'person_handling_duties_id': self.person_handling_duties_id,
            'person_handling_name': f"{self.person_handling.first_name} {self.person_handling.last_name}" if self.person_handling else None,
            'handover_notes': self.handover_notes,
            'attachment_path': self.attachment_path
        }
    
    def __repr__(self):
        return f'<LeaveApplication {self.id}: {self.user_id} - {self.status}>'