"""fix_cliente_id_nullable

Revision ID: 0011_fix_cliente_id_nullable
Revises: 0010_add_invoice_type_fields
Create Date: 2026-05-26 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "0011_fix_cliente_id_nullable"
down_revision = "0010_add_invoice_type_fields"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("erp_fatture") as batch_op:
        batch_op.alter_column("cliente_id", existing_type=sa.Integer(), nullable=True)


def downgrade():
    with op.batch_alter_table("erp_fatture") as batch_op:
        batch_op.alter_column("cliente_id", existing_type=sa.Integer(), nullable=False)
