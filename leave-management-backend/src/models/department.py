from src.extensions import db
from datetime import datetime, timezone

class Department(db.Model):
    __tablename__ = 'departments'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    head_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    is_active = db.Column(db.Boolean, default=True)

    # Relationships - NO back_populates to avoid circular issues
    head = db.relationship('User', foreign_keys=[head_id], back_populates='headed_department')

    def to_dict(self):
        """Convert department to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'head_id': self.head_id,
            'head_name': f"{self.head.first_name} {self.head.last_name}" if self.head else None,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        return f'<Department {self.name}>'