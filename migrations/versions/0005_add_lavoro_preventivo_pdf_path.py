"""add preventivo_pdf_path to lavori

Revision ID: 0005_add_lavoro_preventivo_pdf_path
Revises: 0004_add_editorial_publication_images
Create Date: 2026-05-08 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "0005_add_lavoro_preventivo_pdf_path"
down_revision = "0004_add_editorial_publication_images"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = [col["name"] for col in inspector.get_columns("lavori")]
    if "preventivo_pdf_path" not in columns:
        op.add_column(
            "lavori",
            sa.Column("preventivo_pdf_path", sa.String(length=255), nullable=True),
        )


def downgrade():
    op.drop_column("lavori", "preventivo_pdf_path")
