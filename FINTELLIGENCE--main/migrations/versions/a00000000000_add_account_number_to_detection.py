"""add account_number to detection_results

Revision ID: a00000000000
Revises: ff861b0f538b
Create Date: 2026-07-04 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a00000000000'
down_revision = 'ff861b0f538b'
branch_labels = None
depends_on = None


def upgrade():
    # Add account_number column
    with op.batch_alter_table('detection_results') as batch_op:
        batch_op.add_column(sa.Column('account_number', sa.String(length=255), nullable=True))
        batch_op.alter_column('statement_id',
                   existing_type=sa.String(length=36),
                   nullable=True)


def downgrade():
    with op.batch_alter_table('detection_results') as batch_op:
        batch_op.alter_column('statement_id',
                   existing_type=sa.String(length=36),
                   nullable=False)
        batch_op.drop_column('account_number')
