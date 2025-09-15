# src/models/notification.py
from datetime import datetime, timezone
from src.extensions import db

class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(50), nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    
    leave_application_id = db.Column(db.Integer, db.ForeignKey('leave_applications.id'), nullable=True)
    
    # Relationships - NO back_populates to avoid circular issues
    user = db.relationship('User', foreign_keys=[user_id])
    leave_application = db.relationship('LeaveApplication', foreign_keys=[leave_application_id])

    def to_dict(self):
        """Convert notification to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'message': self.message,
            'notification_type': self.notification_type,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'leave_application_id': self.leave_application_id
        }
    
    def mark_as_read(self):
        """Mark notification as read"""
        self.is_read = True
        db.session.commit()
    
    @classmethod
    def create_leave_application_notification(cls, user_id, leave_application):
        """Create notification for new leave application"""
        notification = cls(
            user_id=user_id,
            title="New Leave Application",
            message=f"New leave application from {leave_application.user.full_name} for {leave_application.leave_type.name}",  # FIXED: use .user not .applicant
            notification_type="leave_application",
            leave_application_id=leave_application.id
        )
        db.session.add(notification)
        return notification
    
    @classmethod
    def create_leave_approval_notification(cls, user_id, leave_application, approver):
        """Create notification for leave approval"""
        notification = cls(
            user_id=user_id,
            title="Leave Application Approved",
            message=f"Your {leave_application.leave_type.name} application has been approved by {approver.full_name}",
            notification_type="leave_approval",
            leave_application_id=leave_application.id
        )
        db.session.add(notification)
        return notification
    
    @classmethod
    def create_leave_rejection_notification(cls, user_id, leave_application, rejector, comments=None):
        """Create notification for leave rejection"""
        message = f"Your {leave_application.leave_type.name} application has been rejected by {rejector.full_name}"
        if comments:
            message += f". Reason: {comments}"
        
        notification = cls(
            user_id=user_id,
            title="Leave Application Rejected",
            message=message,
            notification_type="leave_rejection",
            leave_application_id=leave_application.id
        )
        db.session.add(notification)
        return notification
    
    @classmethod
    def create_leave_balance_exhausted_notification(cls, user_id, leave_type_name):
        """Create notification for exhausted leave balance"""
        notification = cls(
            user_id=user_id,
            title="Leave Balance Exhausted",
            message=f"Your {leave_type_name} leave balance has been exhausted. You cannot apply for more leave of this type.",
            notification_type="system"
        )
        db.session.add(notification)
        return notification
    
    @classmethod
    def get_user_notifications(cls, user_id, limit=50):
        """Get notifications for a user"""
        return cls.query.filter_by(user_id=user_id).order_by(
            cls.created_at.desc()
        ).limit(limit).all()
    
    @classmethod
    def get_unread_count(cls, user_id):
        """Get count of unread notifications for a user"""
        return cls.query.filter_by(user_id=user_id, is_read=False).count()
    
    def __repr__(self):
        return f'<Notification {self.id} - {self.title} - {"Read" if self.is_read else "Unread"}>'