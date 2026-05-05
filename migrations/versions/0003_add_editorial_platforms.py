"""add editorial publication platforms

Revision ID: 0003_add_editorial_platforms
Revises: 0002_add_editorial_publications
Create Date: 2026-05-05 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "0003_add_editorial_platforms"
down_revision = "0002_add_editorial_publications"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {
        column["name"]
        for column in inspector.get_columns("erp_editorial_publications")
    }
    if "platforms" not in columns:
        with op.batch_alter_table("erp_editorial_publications") as batch_op:
            batch_op.add_column(sa.Column("platforms", sa.String(length=200), nullable=True))

    op.execute(
        """
        UPDATE erp_editorial_publications
        SET platforms = platform
        WHERE (platforms IS NULL OR platforms = '')
          AND platform IS NOT NULL
          AND platform != ''
        """
    )


def downgrade():
    pass
