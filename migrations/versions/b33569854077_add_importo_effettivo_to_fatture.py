"""add importo_effettivo to fatture

Revision ID: b33569854077
Revises: 0013_sync_existing_paid_received_invoices
Create Date: 2026-05-29 01:09:03.221758

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b33569854077'
down_revision = '0013_sync_existing_paid_received_invoices'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('erp_fatture', schema=None) as batch_op:
        batch_op.add_column(sa.Column('importo_effettivo', sa.Numeric(precision=12, scale=2), nullable=True))


def downgrade():
    with op.batch_alter_table('erp_fatture', schema=None) as batch_op:
        batch_op.drop_column('importo_effettivo')
