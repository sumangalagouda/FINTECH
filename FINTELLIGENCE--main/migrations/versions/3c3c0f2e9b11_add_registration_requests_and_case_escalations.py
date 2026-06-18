"""add registration_requests and case_escalations

Revision ID: 3c3c0f2e9b11
Revises: 5ba7200e54a1
Create Date: 2026-06-18

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '3c3c0f2e9b11'
down_revision = '5ba7200e54a1'
branch_labels = None
depends_on = None


def upgrade():
    # registration_requests
    op.create_table(
        'registration_requests',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=120), nullable=False),
        sa.Column('employee_id', sa.String(length=100), nullable=False),
        sa.Column('organization', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('requested_role', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('requested_at', sa.DateTime(), nullable=False),
        sa.Column('reviewed_by', sa.String(length=36), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['reviewed_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # case_escalations
    op.create_table(
        'case_escalations',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('case_id', sa.String(length=36), nullable=False),
        sa.Column('escalated_by', sa.String(length=36), nullable=False),
        sa.Column('escalated_to', sa.String(length=36), nullable=True),
        sa.Column('escalation_reason', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('reviewed_by', sa.String(length=36), nullable=True),
        sa.Column('reviewer_notes', sa.Text(), nullable=True),
        sa.Column('fir_recommended', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['case_id'], ['cases.id'], ),
        sa.ForeignKeyConstraint(['escalated_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['escalated_to'], ['users.id'], ),
        sa.ForeignKeyConstraint(['reviewed_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Optional indexes can be added later if needed.


def downgrade():
    op.drop_table('case_escalations')
    op.drop_table('registration_requests')

