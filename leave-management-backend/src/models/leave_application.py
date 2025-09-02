# src/models/leave_application.py
from datetime import datetime, timezone
from src.extensions import db

class LeaveApplication(db.Model):
    __tablename__ = 'leave_applications'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Basic application info
    applicant_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    leave_type_id = db.Column(db.Integer, db.ForeignKey('leave_types.id'), nullable=False)
    subject = db.Column(db.String(255), nullable=True)
    
    # Date information
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    days_requested = db.Column(db.Integer, nullable=False)
    
    # Last leave information
    last_leave_from = db.Column(db.Date, nullable=True)
    last_leave_to = db.Column(db.Date, nullable=True)
    
    # Contact and payment info
    contact_info = db.Column(db.Text, nullable=True)
    salary_payment_preference = db.Column(db.String(50), default='bank_account')  # 'bank_account' or 'address'
    salary_payment_address = db.Column(db.Text, nullable=True)
    
    # Permission and duty handover
    permission_note_country = db.Column(db.Text, nullable=True)
    person_handling_duties_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Status and approval workflow
    status = db.Column(db.String(50), default='pending')  # pending, pending_hod_approval, pending_principal_secretary_approval, approved, rejected
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # HOD approval
    hod_approved = db.Column(db.Boolean, default=False)
    hod_approval_date = db.Column(db.DateTime, nullable=True)
    hod_comments = db.Column(db.Text, nullable=True)
    
    # Principal Secretary approval  
    principal_secretary_approved = db.Column(db.Boolean, default=False)
    principal_secretary_approval_date = db.Column(db.DateTime, nullable=True)
    principal_secretary_comments = db.Column(db.Text, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    
    # PDF generation
    pdf_generated = db.Column(db.Boolean, default=False)
    pdf_path = db.Column(db.String(255), nullable=True)

    # Relationships
    applicant = db.relationship('User', foreign_keys=[applicant_id], back_populates='leave_applications')
    leave_type = db.relationship('LeaveType', back_populates='applications')
    person_handling_duties = db.relationship('User', foreign_keys=[person_handling_duties_id])

    def to_dict(self):
        """Convert leave application to dictionary"""
        return {
            'id': self.id,
            'applicant_id': self.applicant_id,
            'applicant_name': self.applicant.full_name if self.applicant else None,
            'applicant_employee_number': self.applicant.employee_number if self.applicant else None,
            'leave_type_id': self.leave_type_id,
            'leave_type_name': self.leave_type.name if self.leave_type else None,
            'subject': self.subject,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'days_requested': self.days_requested,
            'last_leave_from': self.last_leave_from.isoformat() if self.last_leave_from else None,
            'last_leave_to': self.last_leave_to.isoformat() if self.last_leave_to else None,
            'contact_info': self.contact_info,
            'salary_payment_preference': self.salary_payment_preference,
            'salary_payment_address': self.salary_payment_address,
            'permission_note_country': self.permission_note_country,
            'person_handling_duties_id': self.person_handling_duties_id,
            'person_handling_duties_name': self.person_handling_duties.full_name if self.person_handling_duties else None,
            'status': self.status,
            'hod_approved': self.hod_approved,
            'hod_approval_date': self.hod_approval_date.isoformat() if self.hod_approval_date else None,
            'hod_comments': self.hod_comments,
            'principal_secretary_approved': self.principal_secretary_approved,
            'principal_secretary_approval_date': self.principal_secretary_approval_date.isoformat() if self.principal_secretary_approval_date else None,
            'principal_secretary_comments': self.principal_secretary_comments,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'pdf_generated': self.pdf_generated,
            'pdf_path': self.pdf_path
        }

    def get_approval_status(self):
        """Get detailed approval status"""
        if self.status == 'approved':
            return 'Fully Approved'
        elif self.status == 'rejected':
            return 'Rejected'
        elif self.status == 'pending_hod_approval':
            return 'Pending HOD Approval'
        elif self.status == 'pending_principal_secretary_approval':
            return 'Pending Principal Secretary Approval'
        else:
            return 'Pending'

    def can_be_approved_by(self, user):
        """Check if user can approve this application"""
        if user.role == 'hod' and self.status == 'pending_hod_approval':
            return self.applicant.role == 'staff'
        elif user.role == 'principal_secretary' and self.status == 'pending_principal_secretary_approval':
            return self.applicant.role in ['staff', 'hod']
        return False

    def is_current_leave(self):
        """Check if this is a current active leave"""
        from datetime import date
        today = date.today()
        return (self.status == 'approved' and 
                self.start_date <= today <= self.end_date)

    def is_upcoming_leave(self):
        """Check if this is an upcoming approved leave"""
        from datetime import date
        today = date.today()
        return (self.status == 'approved' and 
                self.start_date > today)

    def __repr__(self):
        return f'<LeaveApplication {self.id} - {self.applicant.full_name if self.applicant else "Unknown"} - {self.status}>'