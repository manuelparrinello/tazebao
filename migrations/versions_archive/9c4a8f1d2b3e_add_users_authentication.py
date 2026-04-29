"""add users authentication

Revision ID: 9c4a8f1d2b3e
Revises: 7b80d702c52a
Create Date: 2026-04-28 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "9c4a8f1d2b3e"
down_revision = "7b80d702c52a"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "users" not in inspector.get_table_names():
        op.create_table(
            "users",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(length=100), nullable=True),
            sa.Column("email", sa.String(length=255), nullable=False),
            sa.Column("password_hash", sa.String(length=255), nullable=False),
            sa.Column("role", sa.String(length=20), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
            sa.UniqueConstraint("email", name=op.f("uq_users_email")),
        )
        op.create_index(op.f("ix_users_email"), "users", ["email"], unique=False)


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "users" in inspector.get_table_names():
        indexes = {index["name"] for index in inspector.get_indexes("users")}
        if op.f("ix_users_email") in indexes:
            op.drop_index(op.f("ix_users_email"), table_name="users")
        op.drop_table("users")
