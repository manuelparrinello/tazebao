"""add_aliquota_iva_to_fatture

Revision ID: 0008_add_aliquota_iva
Revises: 36a67110cca5
Create Date: 2026-05-20 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "0008_add_aliquota_iva"
down_revision = "36a67110cca5"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "erp_fatture",
        sa.Column("aliquota_iva", sa.Integer(), nullable=False, server_default="22"),
    )


def downgrade():
    op.drop_column("erp_fatture", "aliquota_iva")
