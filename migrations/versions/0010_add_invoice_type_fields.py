"""add_invoice_type_fields_to_fatture

Revision ID: 0010_add_invoice_type_fields
Revises: 0009_add_notifications_read_at
Create Date: 2026-05-26 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "0010_add_invoice_type_fields"
down_revision = "0009_add_notifications_read_at"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("erp_fatture") as batch_op:
        batch_op.add_column(sa.Column("invoice_type", sa.String(10), nullable=False, server_default="sent"))
        batch_op.add_column(sa.Column("fornitore", sa.String(200), nullable=True))
        batch_op.add_column(sa.Column("stato_pagamento", sa.String(20), nullable=True))
        batch_op.alter_column("cliente_id", existing_type=sa.Integer(), nullable=True)
        batch_op.create_index("ix_fatture_invoice_type", ["invoice_type"])


def downgrade():
    with op.batch_alter_table("erp_fatture") as batch_op:
        batch_op.drop_index("ix_fatture_invoice_type")
        batch_op.alter_column("cliente_id", existing_type=sa.Integer(), nullable=False)
        batch_op.drop_column("stato_pagamento")
        batch_op.drop_column("fornitore")
        batch_op.drop_column("invoice_type")
