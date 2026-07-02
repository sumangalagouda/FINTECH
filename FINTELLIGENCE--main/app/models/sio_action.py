import uuid
from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import JSON
from app.extensions import db


class SIOAction(db.Model):
    __tablename__ = 'sio_actions'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id = db.Column(db.String(36), db.ForeignKey('cases.id'), nullable=False)
    signature_id = db.Column(db.String(36), db.ForeignKey('digital_signatures.id'), nullable=False)
    decision = db.Column(db.String(50), nullable=False)  # recommend_fir / close_insufficient_evidence / return_to_io / escalate_external
    authority = db.Column(db.String(255), nullable=True)
    ipc_sections = db.Column(JSON, nullable=False, default=list)
    remarks = db.Column(db.Text, nullable=False)
    submission_authority = db.Column(db.String(255), nullable=True)  # final recommended authority for submission
    created_by = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    notified_io = db.Column(db.Boolean, default=False)

    # Relationships
    case = db.relationship('Case', foreign_keys=[case_id], backref='sio_actions')
    signature = db.relationship('DigitalSignature', foreign_keys=[signature_id], backref='sio_action')
    creator = db.relationship('User', foreign_keys=[created_by], backref='sio_actions_created')

    def __repr__(self):
        return f'<SIOAction {self.decision} on {self.created_at.isoformat()}>'
