"""add account_scores to case

Revision ID: b00000000000
Revises: a00000000000
Create Date: 2026-07-04 12:10:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'b00000000000'
down_revision = 'a00000000000'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('cases') as batch_op:
        batch_op.add_column(sa.Column('account_scores', postgresql.JSON(astext_type=sa.Text()), nullable=True))

def downgrade():
    with op.batch_alter_table('cases') as batch_op:
        batch_op.drop_column('account_scores')
