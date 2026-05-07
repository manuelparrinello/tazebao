"""add editorial publication images table

Revision ID: 0004_add_editorial_publication_images
Revises: 0003_add_editorial_platforms
Create Date: 2026-05-08 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "0004_add_editorial_publication_images"
down_revision = "0003_add_editorial_platforms"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()

    if "erp_editorial_publication_images" not in tables:
        op.create_table(
            "erp_editorial_publication_images",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("publication_id", sa.Integer(), nullable=False),
            sa.Column("image_path", sa.String(length=500), nullable=False),
            sa.Column("sort_order", sa.Integer(), nullable=False, server_default=sa.text("0")),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(
                ["publication_id"],
                ["erp_editorial_publications.id"],
                name=op.f("fk_erp_editorial_publication_images_publication_id"),
            ),
            sa.PrimaryKeyConstraint("id", name=op.f("pk_erp_editorial_publication_images")),
        )
        op.create_index(
            op.f("ix_erp_editorial_publication_images_publication_id"),
            "erp_editorial_publication_images",
            ["publication_id"],
            unique=False,
        )

    op.execute(
        """
        INSERT INTO erp_editorial_publication_images (publication_id, image_path, sort_order, created_at)
        SELECT id, preview_image_path, 0, created_at
        FROM erp_editorial_publications
        WHERE preview_image_path IS NOT NULL AND preview_image_path != ''
          AND id NOT IN (
              SELECT publication_id FROM erp_editorial_publication_images
          )
        """
    )


def downgrade():
    pass
