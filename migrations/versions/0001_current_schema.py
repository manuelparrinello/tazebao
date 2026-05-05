"""current schema baseline

Revision ID: 0001_current_schema
Revises:
Create Date: 2026-04-29 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "0001_current_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
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
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    op.create_table(
        "clienti",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("ragsoc", sa.String(length=100), nullable=False),
        sa.Column("indirizzo", sa.String(length=100), nullable=True),
        sa.Column("citta", sa.String(length=50), nullable=True),
        sa.Column("cap", sa.String(length=5), nullable=True),
        sa.Column("provincia", sa.String(length=2), nullable=True),
        sa.Column("email", sa.String(length=100), nullable=False),
        sa.Column("telefono", sa.String(length=20), nullable=False),
        sa.Column("p_iva", sa.String(length=30), nullable=True),
        sa.Column("sdi", sa.String(length=7), nullable=True),
        sa.Column("pec", sa.String(length=100), nullable=True),
        sa.Column("colore", sa.String(length=20), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_clienti")),
    )

    op.create_table(
        "lavori",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("descrizione", sa.String(length=200), nullable=False),
        sa.Column("data_inizio", sa.Date(), nullable=True),
        sa.Column("data_fine", sa.Date(), nullable=True),
        sa.Column("data_pagamento", sa.Date(), nullable=True),
        sa.Column("stato", sa.String(length=50), nullable=True),
        sa.Column("priorita", sa.String(length=50), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("preventivato", sa.Float(), nullable=True),
        sa.Column("cliente_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["cliente_id"],
            ["clienti.id"],
            name=op.f("fk_lavori_cliente_id_clienti"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_lavori")),
    )

    op.create_table(
        "tasks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("tipo", sa.String(length=20), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=True),
        sa.Column("lavoro_id", sa.Integer(), nullable=False),
        sa.Column("note", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["lavoro_id"],
            ["lavori.id"],
            name=op.f("fk_tasks_lavoro_id_lavori"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_tasks")),
    )

    op.create_table(
        "taskfile",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("filename", sa.String(length=100), nullable=False),
        sa.Column("tipo", sa.String(length=20), nullable=False),
        sa.Column("size", sa.Float(), nullable=False),
        sa.Column("task_id", sa.Integer(), nullable=False),
        sa.Column("note", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["task_id"],
            ["tasks.id"],
            name=op.f("fk_taskfile_task_id_tasks"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_taskfile")),
    )

    op.create_table(
        "erp_tasks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("category", sa.String(length=40), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("priority", sa.String(length=40), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("lavoro_id", sa.Integer(), nullable=True),
        sa.Column("cliente_id", sa.Integer(), nullable=True),
        sa.Column("assignee_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["assignee_id"],
            ["users.id"],
            name=op.f("fk_erp_tasks_assignee_id_users"),
        ),
        sa.ForeignKeyConstraint(
            ["cliente_id"],
            ["clienti.id"],
            name=op.f("fk_erp_tasks_cliente_id_clienti"),
        ),
        sa.ForeignKeyConstraint(
            ["lavoro_id"],
            ["lavori.id"],
            name=op.f("fk_erp_tasks_lavoro_id_lavori"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_erp_tasks")),
    )

    op.create_table(
        "preventivi",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("descrizione", sa.String(length=200), nullable=False),
        sa.Column("cliente_id", sa.Integer(), nullable=False),
        sa.Column("data_creazione", sa.DateTime(), nullable=False),
        sa.Column("stato", sa.String(length=20), nullable=False),
        sa.Column("totale_preventivo", sa.Float(), nullable=True),
        sa.Column("lavoro_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["cliente_id"],
            ["clienti.id"],
            name=op.f("fk_preventivi_cliente_id_clienti"),
        ),
        sa.ForeignKeyConstraint(
            ["lavoro_id"],
            ["lavori.id"],
            name=op.f("fk_preventivi_lavoro_id_lavori"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_preventivi")),
    )

    op.create_table(
        "righe_preventivo",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("qty", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("descrizione", sa.Text(), nullable=False),
        sa.Column("prezzo_ie", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("prezzo_ii", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("totale_riga", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("preventivo_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["preventivo_id"],
            ["preventivi.id"],
            name=op.f("fk_righe_preventivo_preventivo_id_preventivi"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_righe_preventivo")),
    )

    op.create_table(
        "erp_calendar_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("event_type", sa.String(length=40), nullable=False),
        sa.Column("start_datetime", sa.DateTime(), nullable=False),
        sa.Column("end_datetime", sa.DateTime(), nullable=True),
        sa.Column("cliente_id", sa.Integer(), nullable=True),
        sa.Column("lavoro_id", sa.Integer(), nullable=True),
        sa.Column("task_id", sa.Integer(), nullable=True),
        sa.Column("assigned_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["assigned_user_id"],
            ["users.id"],
            name=op.f("fk_erp_calendar_events_assigned_user_id_users"),
        ),
        sa.ForeignKeyConstraint(
            ["cliente_id"],
            ["clienti.id"],
            name=op.f("fk_erp_calendar_events_cliente_id_clienti"),
        ),
        sa.ForeignKeyConstraint(
            ["lavoro_id"],
            ["lavori.id"],
            name=op.f("fk_erp_calendar_events_lavoro_id_lavori"),
        ),
        sa.ForeignKeyConstraint(
            ["task_id"],
            ["erp_tasks.id"],
            name=op.f("fk_erp_calendar_events_task_id_erp_tasks"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_erp_calendar_events")),
    )

    op.create_table(
        "erp_editorial_publications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("cliente_id", sa.Integer(), nullable=False),
        sa.Column("publication_date", sa.Date(), nullable=False),
        sa.Column("platform", sa.String(length=40), nullable=False),
        sa.Column("platforms", sa.String(length=200), nullable=True),
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

    op.create_table(
        "erp_financial_movements",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("movement_type", sa.String(length=20), nullable=False),
        sa.Column("movement_status", sa.String(length=20), nullable=False),
        sa.Column("expense_type", sa.String(length=20), nullable=True),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("movement_date", sa.Date(), nullable=False),
        sa.Column("month", sa.Integer(), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("cliente_id", sa.Integer(), nullable=True),
        sa.Column("lavoro_id", sa.Integer(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["cliente_id"],
            ["clienti.id"],
            name=op.f("fk_erp_financial_movements_cliente_id_clienti"),
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
            name=op.f("fk_erp_financial_movements_created_by_users"),
        ),
        sa.ForeignKeyConstraint(
            ["lavoro_id"],
            ["lavori.id"],
            name=op.f("fk_erp_financial_movements_lavoro_id_lavori"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_erp_financial_movements")),
    )

    op.create_table(
        "erp_email_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("subject", sa.String(length=255), nullable=False),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("direction", sa.String(length=20), nullable=False),
        sa.Column("email_address", sa.String(length=255), nullable=False),
        sa.Column("cliente_id", sa.Integer(), nullable=True),
        sa.Column("lavoro_id", sa.Integer(), nullable=True),
        sa.Column("task_id", sa.Integer(), nullable=True),
        sa.Column("sent_at", sa.DateTime(), nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("message_id", sa.String(length=255), nullable=True),
        sa.Column("thread_id", sa.String(length=255), nullable=True),
        sa.Column("provider", sa.String(length=80), nullable=True),
        sa.Column("provider_account", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["cliente_id"],
            ["clienti.id"],
            name=op.f("fk_erp_email_logs_cliente_id_clienti"),
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
            name=op.f("fk_erp_email_logs_created_by_users"),
        ),
        sa.ForeignKeyConstraint(
            ["lavoro_id"],
            ["lavori.id"],
            name=op.f("fk_erp_email_logs_lavoro_id_lavori"),
        ),
        sa.ForeignKeyConstraint(
            ["task_id"],
            ["erp_tasks.id"],
            name=op.f("fk_erp_email_logs_task_id_erp_tasks"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_erp_email_logs")),
    )
    op.create_index(
        op.f("ix_erp_email_logs_email_address"),
        "erp_email_logs",
        ["email_address"],
        unique=False,
    )
    op.create_index(
        op.f("ix_erp_email_logs_message_id"),
        "erp_email_logs",
        ["message_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_erp_email_logs_thread_id"),
        "erp_email_logs",
        ["thread_id"],
        unique=False,
    )

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
    op.create_index(
        op.f("ix_erp_email_accounts_email_address"),
        "erp_email_accounts",
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
    op.create_index(
        op.f("ix_erp_email_messages_message_id"),
        "erp_email_messages",
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
    op.drop_index(op.f("ix_erp_email_messages_message_id"), table_name="erp_email_messages")
    op.drop_table("erp_email_messages")
    op.drop_index(
        op.f("ix_erp_email_accounts_email_address"),
        table_name="erp_email_accounts",
    )
    op.drop_table("erp_email_accounts")
    op.drop_index(op.f("ix_erp_email_logs_thread_id"), table_name="erp_email_logs")
    op.drop_index(op.f("ix_erp_email_logs_message_id"), table_name="erp_email_logs")
    op.drop_index(op.f("ix_erp_email_logs_email_address"), table_name="erp_email_logs")
    op.drop_table("erp_email_logs")
    op.drop_table("erp_financial_movements")
    op.drop_index(
        "ix_editorial_publications_cliente_date_platform",
        table_name="erp_editorial_publications",
    )
    op.drop_index(
        "ix_editorial_publications_cliente_date",
        table_name="erp_editorial_publications",
    )
    op.drop_index(
        op.f("ix_erp_editorial_publications_status"),
        table_name="erp_editorial_publications",
    )
    op.drop_index(
        op.f("ix_erp_editorial_publications_publication_date"),
        table_name="erp_editorial_publications",
    )
    op.drop_index(
        op.f("ix_erp_editorial_publications_platform"),
        table_name="erp_editorial_publications",
    )
    op.drop_index(
        op.f("ix_erp_editorial_publications_cliente_id"),
        table_name="erp_editorial_publications",
    )
    op.drop_index(
        op.f("ix_erp_editorial_publications_assigned_user_id"),
        table_name="erp_editorial_publications",
    )
    op.drop_table("erp_editorial_publications")
    op.drop_table("erp_calendar_events")
    op.drop_table("righe_preventivo")
    op.drop_table("preventivi")
    op.drop_table("erp_tasks")
    op.drop_table("taskfile")
    op.drop_table("tasks")
    op.drop_table("lavori")
    op.drop_table("clienti")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
