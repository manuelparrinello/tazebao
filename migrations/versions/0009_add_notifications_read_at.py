"""add_notifications_read_at_to_users

Revision ID: 0009_add_notifications_read_at
Revises: 0008_add_aliquota_iva
Create Date: 2026-05-23 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "0009_add_notifications_read_at"
down_revision = "0008_add_aliquota_iva"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "users",
        sa.Column("notifications_read_at", sa.DateTime(), nullable=True),
    )


def downgrade():
    op.drop_column("users", "notifications_read_at")
