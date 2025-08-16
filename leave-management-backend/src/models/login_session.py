from datetime import datetime, timezone
from src.extensions import db

class LoginSession(db.Model):
    __tablename__ = 'login_sessions'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    login_time = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)

    user = db.relationship('User', back_populates='login_sessions')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'login_time': self.login_time.isoformat() if self.login_time else None,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent
        }

