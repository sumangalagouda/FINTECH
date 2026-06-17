import uuid
from datetime import datetime, timezone
from app.extensions import db

class CaseGraph(db.Model):
    __tablename__ = 'case_graphs'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id = db.Column(db.String(36), db.ForeignKey('cases.id'), nullable=False)
    graph_type = db.Column(db.String(50), nullable=False, default='unified')
    graph_data = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    case = db.relationship('Case', backref='graphs', lazy=True)

    def __repr__(self):
        return f'<CaseGraph {self.id} for Case {self.case_id}>'
