"""add editorial publications

Revision ID: 0002_add_editorial_publications
Revises: 0001_current_schema
Create Date: 2026-05-05 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "0002_add_editorial_publications"
down_revision = "0001_current_schema"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "erp_editorial_publications" in inspector.get_table_names():
        return

    op.create_table(
        "erp_editorial_publications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("cliente_id", sa.Integer(), nullable=False),
        sa.Column("publication_date", sa.Date(), nullable=False),
        sa.Column("platform", sa.String(length=40), nullable=False),
        sa.Column("content_type", sa.String(length=40), nullable=False),
        sa.Column("title", sa.String(length=180), nullable=False),
        sa.Column("caption", sa.Text(), nullable=True),
        sa.Column("preview_image_path", sa.String(length=500), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("assigned_user_id", sa.Integer(), nullable=True),
        sa.Column("client_approval_status", sa.String(length=40), nullable=False),
        sa.Column("internal_notes", sa.Text(), nullable=True),
        sa.Column("asset_url", sa.String(length=1000), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["assigned_user_id"],
            ["users.id"],
            name=op.f("fk_erp_editorial_publications_assigned_user_id_users"),
        ),
        sa.ForeignKeyConstraint(
            ["cliente_id"],
            ["clienti.id"],
            name=op.f("fk_erp_editorial_publications_cliente_id_clienti"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_erp_editorial_publications")),
    )
    op.create_index(
        op.f("ix_erp_editorial_publications_assigned_user_id"),
        "erp_editorial_publications",
        ["assigned_user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_erp_editorial_publications_cliente_id"),
        "erp_editorial_publications",
        ["cliente_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_erp_editorial_publications_platform"),
        "erp_editorial_publications",
        ["platform"],
        unique=False,
    )
    op.create_index(
        op.f("ix_erp_editorial_publications_publication_date"),
        "erp_editorial_publications",
        ["publication_date"],
        unique=False,
    )
    op.create_index(
        op.f("ix_erp_editorial_publications_status"),
        "erp_editorial_publications",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_editorial_publications_cliente_date",
        "erp_editorial_publications",
        ["cliente_id", "publication_date"],
        unique=False,
    )
    op.create_index(
        "ix_editorial_publications_cliente_date_platform",
        "erp_editorial_publications",
        ["cliente_id", "publication_date", "platform"],
        unique=False,
    )


def downgrade():
    pass
