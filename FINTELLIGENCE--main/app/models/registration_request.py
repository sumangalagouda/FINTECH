import uuid
from datetime import datetime, timezone

from app.extensions import db


class RegistrationRequest(db.Model):
    __tablename__ = 'registration_requests'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    employee_id = db.Column(db.String(100), nullable=False)
    organization = db.Column(db.String(255), nullable=False)

    password_hash = db.Column(db.String(255), nullable=False)

    requested_role = db.Column(db.String(50), nullable=False)  # investigator/supervisor
    status = db.Column(db.String(50), default='pending', nullable=False)  # pending/approved/rejected

    requested_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    reviewed_by = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    reviewed_at = db.Column(db.DateTime, nullable=True)

    # Helpful indexes/constraints can be added via migration if needed.
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def __repr__(self):
        return f'<RegistrationRequest {self.email} {self.status}>'

