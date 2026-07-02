import uuid
from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import JSON
from app.extensions import db


class DigitalSignature(db.Model):
    __tablename__ = 'digital_signatures'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id = db.Column(db.String(36), db.ForeignKey('cases.id'), nullable=False)
    signed_by = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    signer_role = db.Column(db.String(50), nullable=False)  # io / sr_io / supervisor / admin
    decision = db.Column(db.String(50), nullable=False)  # recommend_fir / close_insufficient_evidence / return_to_io / escalate_external
    authority = db.Column(db.String(255), nullable=True)  # e.g. "Economic Offences Wing", "ED", "FIU"
    ipc_sections = db.Column(JSON, nullable=False, default=list)  # ["IPC 420", "PMLA Section 3"]
    remarks = db.Column(db.Text, nullable=False)
    signature_hash = db.Column(db.String(64), nullable=False, unique=True)  # SHA-256 hex string
    suspicion_score_at_signing = db.Column(db.Float, nullable=False)
    is_override = db.Column(db.Boolean, default=False)  # true if score was below threshold
    signed_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    signer = db.relationship('User', foreign_keys=[signed_by], backref='digital_signatures')
    case = db.relationship('Case', foreign_keys=[case_id], backref='digital_signatures')

    def __repr__(self):
        return f'<DigitalSignature {self.id[:8]}... by {self.signer_role} on {self.signed_at.isoformat()}>'
