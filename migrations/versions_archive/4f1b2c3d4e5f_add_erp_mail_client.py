"""add erp mail client

Revision ID: 4f1b2c3d4e5f
Revises: 29a2b319a499
Create Date: 2026-04-28 19:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "4f1b2c3d4e5f"
down_revision = "29a2b319a499"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "erp_email_accounts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("label", sa.String(length=120), nullable=False),
        sa.Column("email_address", sa.String(length=255), nullable=False),
        sa.Column("imap_host", sa.String(length=255), nullable=False),
        sa.Column("imap_port", sa.Integer(), nullable=False),
        sa.Column("imap_use_ssl", sa.Boolean(), nullable=False),
        sa.Column("smtp_host", sa.String(length=255), nullable=False),
        sa.Column("smtp_port", sa.Integer(), nullable=False),
        sa.Column("smtp_use_tls", sa.Boolean(), nullable=False),
        sa.Column("username", sa.String(length=255), nullable=False),
        sa.Column("password_encrypted", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("last_sync_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
            name=op.f("fk_erp_email_accounts_created_by_users"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_erp_email_accounts")),
    )
    with op.batch_alter_table("erp_email_accounts", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_erp_email_accounts_email_address"),
            ["email_address"],
            unique=False,
        )

    op.create_table(
        "erp_email_messages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("account_id", sa.Integer(), nullable=False),
        sa.Column("message_id", sa.String(length=512), nullable=True),
        sa.Column("imap_uid", sa.String(length=120), nullable=True),
        sa.Column("folder", sa.String(length=120), nullable=False),
        sa.Column("subject", sa.String(length=500), nullable=True),
        sa.Column("from_address", sa.String(length=500), nullable=True),
        sa.Column("to_addresses", sa.Text(), nullable=True),
        sa.Column("cc_addresses", sa.Text(), nullable=True),
        sa.Column("reply_to", sa.String(length=500), nullable=True),
        sa.Column("body_text", sa.Text(), nullable=True),
        sa.Column("body_html", sa.Text(), nullable=True),
        sa.Column("direction", sa.String(length=20), nullable=False),
        sa.Column("is_read", sa.Boolean(), nullable=False),
        sa.Column("sent_at", sa.DateTime(), nullable=True),
        sa.Column("received_at", sa.DateTime(), nullable=True),
        sa.Column("cliente_id", sa.Integer(), nullable=True),
        sa.Column("lavoro_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["erp_email_accounts.id"],
            name=op.f("fk_erp_email_messages_account_id_erp_email_accounts"),
        ),
        sa.ForeignKeyConstraint(
            ["cliente_id"],
            ["clienti.id"],
            name=op.f("fk_erp_email_messages_cliente_id_clienti"),
        ),
        sa.ForeignKeyConstraint(
            ["lavoro_id"],
            ["lavori.id"],
            name=op.f("fk_erp_email_messages_lavoro_id_lavori"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_erp_email_messages")),
        sa.UniqueConstraint(
            "account_id",
            "folder",
            "imap_uid",
            name="uq_erp_email_messages_account_folder_uid",
        ),
    )
    with op.batch_alter_table("erp_email_messages", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_erp_email_messages_message_id"),
            ["message_id"],
            unique=False,
        )

    op.create_table(
        "erp_email_attachments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("message_id", sa.Integer(), nullable=False),
        sa.Column("filename", sa.String(length=500), nullable=True),
        sa.Column("content_type", sa.String(length=255), nullable=True),
        sa.Column("size", sa.Integer(), nullable=True),
        sa.Column("storage_path", sa.String(length=1000), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["message_id"],
            ["erp_email_messages.id"],
            name=op.f("fk_erp_email_attachments_message_id_erp_email_messages"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_erp_email_attachments")),
    )


def downgrade():
    op.drop_table("erp_email_attachments")
    with op.batch_alter_table("erp_email_messages", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_erp_email_messages_message_id"))
    op.drop_table("erp_email_messages")
    with op.batch_alter_table("erp_email_accounts", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_erp_email_accounts_email_address"))
    op.drop_table("erp_email_accounts")
