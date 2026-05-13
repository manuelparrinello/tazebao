"""add moodboard tables

Revision ID: 0006_add_moodboard_tables
Revises: 0005_add_lavoro_preventivo_pdf_path
Create Date: 2026-05-12 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "0006_add_moodboard_tables"
down_revision = "0005_add_lavoro_preventivo_pdf_path"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()

    if "erp_moodboards" not in tables:
        op.create_table(
            "erp_moodboards",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("title", sa.String(length=160), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("task_id", sa.Integer(), nullable=True),
            sa.Column("cliente_id", sa.Integer(), nullable=True),
            sa.Column("lavoro_id", sa.Integer(), nullable=True),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(
                ["task_id"],
                ["erp_tasks.id"],
                name=op.f("fk_erp_moodboards_task_id"),
            ),
            sa.ForeignKeyConstraint(
                ["cliente_id"],
                ["clienti.id"],
                name=op.f("fk_erp_moodboards_cliente_id"),
            ),
            sa.ForeignKeyConstraint(
                ["lavoro_id"],
                ["lavori.id"],
                name=op.f("fk_erp_moodboards_lavoro_id"),
            ),
            sa.ForeignKeyConstraint(
                ["created_by"],
                ["users.id"],
                name=op.f("fk_erp_moodboards_created_by"),
            ),
            sa.PrimaryKeyConstraint("id", name=op.f("pk_erp_moodboards")),
        )
        op.create_index(
            op.f("ix_erp_moodboards_task_id"),
            "erp_moodboards",
            ["task_id"],
            unique=False,
        )
        op.create_index(
            op.f("ix_erp_moodboards_cliente_id"),
            "erp_moodboards",
            ["cliente_id"],
            unique=False,
        )
        op.create_index(
            op.f("ix_erp_moodboards_lavoro_id"),
            "erp_moodboards",
            ["lavoro_id"],
            unique=False,
        )

    if "erp_moodboard_images" not in tables:
        op.create_table(
            "erp_moodboard_images",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("moodboard_id", sa.Integer(), nullable=False),
            sa.Column("title", sa.String(length=160), nullable=True),
            sa.Column("image_path", sa.String(length=500), nullable=True),
            sa.Column("image_url", sa.String(length=2000), nullable=True),
            sa.Column("source_type", sa.String(length=10), nullable=False, server_default=sa.text("'upload'")),
            sa.Column("source_url", sa.String(length=2000), nullable=True),
            sa.Column("note", sa.Text(), nullable=True),
            sa.Column("sort_order", sa.Integer(), nullable=False, server_default=sa.text("0")),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(
                ["moodboard_id"],
                ["erp_moodboards.id"],
                name=op.f("fk_erp_moodboard_images_moodboard_id"),
            ),
            sa.PrimaryKeyConstraint("id", name=op.f("pk_erp_moodboard_images")),
        )
        op.create_index(
            op.f("ix_erp_moodboard_images_moodboard_id"),
            "erp_moodboard_images",
            ["moodboard_id"],
            unique=False,
        )


def downgrade():
    pass
