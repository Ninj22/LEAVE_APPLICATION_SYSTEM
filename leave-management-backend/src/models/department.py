from src.extensions import db
from datetime import datetime

class Department(db.Model):
    __tablename__ = 'departments'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    hod_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to User (Head of Department)
    hod = db.relationship('User', foreign_keys=[hod_id], backref='managed_department')
    
    # Relationship to Users (Department members)
    members = db.relationship('User', foreign_keys='User.department_id', backref='department')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'hod_id': self.hod_id,
            'hod_name': f"{self.hod.first_name} {self.hod.last_name}" if self.hod else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        return f'<Department {self.name}>'