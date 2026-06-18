import uuid
from datetime import datetime, timezone

from app.extensions import db


class CaseEscalation(db.Model):
    __tablename__ = 'case_escalations'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    case_id = db.Column(db.String(36), db.ForeignKey('cases.id'), nullable=False)

    escalated_by = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    escalated_to = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)

    escalation_reason = db.Column(db.Text, nullable=True)

    status = db.Column(db.String(50), default='pending', nullable=False)  # pending/under_review/closed

    reviewed_by = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    reviewer_notes = db.Column(db.Text, nullable=True)

    fir_recommended = db.Column(db.Boolean, default=False, nullable=False)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    resolved_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f'<CaseEscalation {self.case_id} {self.status}>'

