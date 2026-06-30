"""add_single_month_to_share_links

Revision ID: 8470cc922350
Revises: f48156ee567e
Create Date: 2026-06-30 15:57:30.547630

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8470cc922350'
down_revision = 'f48156ee567e'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('erp_editorial_share_links', schema=None) as batch_op:
        batch_op.add_column(sa.Column('single_month', sa.Boolean(), nullable=False, server_default=sa.text('0')))


def downgrade():
    with op.batch_alter_table('erp_editorial_share_links', schema=None) as batch_op:
        batch_op.drop_column('single_month')
