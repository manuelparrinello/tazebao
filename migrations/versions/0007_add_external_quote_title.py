"""add external_quote_title and preventivo_pdf_uploaded_at to lavori

Revision ID: 0007_add_external_quote_title
Revises: 1cf1a8df769e
Create Date: 2026-05-19 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "0007_add_external_quote_title"
down_revision = "1cf1a8df769e"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = [col["name"] for col in inspector.get_columns("lavori")]
    if "external_quote_title" not in columns:
        op.add_column(
            "lavori",
            sa.Column("external_quote_title", sa.String(length=200), nullable=True),
        )
    if "preventivo_pdf_uploaded_at" not in columns:
        op.add_column(
            "lavori",
            sa.Column("preventivo_pdf_uploaded_at", sa.DateTime(), nullable=True),
        )


def downgrade():
    op.drop_column("lavori", "preventivo_pdf_uploaded_at")
    op.drop_column("lavori", "external_quote_title")
