from src.extensions import db
from src.models.user import db

class Department(db.Model):
    __tablename__ = 'departments'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    staff_count = db.Column(db.Integer, nullable=False)
    users = db.relationship('User', back_populates='department', lazy=True)
    __table_args__ = {'extend_existing': True}
    hod_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    hod = db.relationship("User", back_populates="department",  foreign_keys=[hod_id])
    staff_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)       
    staff = db.relationship("User", back_populates="department", foreign_keys=[hod_id])

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "hod_id": self.hod_id,
            "hod_name": self.hod.first_name + " " + self.hod.last_name if self.hod else None,
            "staff_count": self.staff_count,
            "staff": [staff.to_dict() for staff in self.staff],
            "staff_names": [staff.first_name + " " + staff.last_name for staff in self.staff],
        }
        
class LoginSession(db.Model):
    __tablename__ = 'login_sessions'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    # Add any other fields you need, for example:
    session_token = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=True)

    # Relationship back to User (optional, if you want to access user from session)
    user = db.relationship('Users', back_populates='login_sessions')   