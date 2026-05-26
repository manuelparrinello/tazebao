"""add_source_fields_to_financial_movements

Revision ID: 0012_add_finance_source_fields
Revises: 0011_fix_cliente_id_nullable
Create Date: 2026-05-27 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "0012_add_finance_source_fields"
down_revision = "0011_fix_cliente_id_nullable"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("erp_financial_movements", sa.Column("source_type", sa.String(30), nullable=True))
    op.add_column("erp_financial_movements", sa.Column("source_id", sa.Integer(), nullable=True))
    op.create_index("ix_financial_source", "erp_financial_movements", ["source_type", "source_id"])


def downgrade():
    op.drop_index("ix_financial_source", table_name="erp_financial_movements")
    op.drop_column("erp_financial_movements", "source_id")
    op.drop_column("erp_financial_movements", "source_type")
