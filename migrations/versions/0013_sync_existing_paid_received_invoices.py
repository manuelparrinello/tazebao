"""sync paid received invoices without financial movement

Revision ID: 0013_sync_existing_paid_received_invoices
Revises: 0012_add_finance_source_fields
Create Date: 2026-05-27 01:00:00.000000

"""
from datetime import date

from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm import Session


revision = "0013_sync_existing_paid_received_invoices"
down_revision = "0012_add_finance_source_fields"
branch_labels = None
depends_on = None


def _parse_date(val):
    if val is None:
        return None
    if isinstance(val, date):
        return val
    if isinstance(val, str):
        return date.fromisoformat(val)
    return val


def upgrade():
    bind = op.get_bind()
    session = Session(bind=bind)

    invoices = session.execute(
        sa.text(
            "SELECT id, numero, fornitore, importo, data_pagamento, data_emissione, note "
            "FROM erp_fatture "
            "WHERE invoice_type = 'received' AND stato_pagamento = 'pagata'"
        )
    ).fetchall()

    for row in invoices:
        existing = session.execute(
            sa.text(
                "SELECT id FROM erp_financial_movements "
                "WHERE source_type = 'received_invoice' AND source_id = :sid"
            ),
            {"sid": row.id},
        ).fetchone()
        if existing:
            continue

        data_pag = _parse_date(row.data_pagamento)
        data_em = _parse_date(row.data_emissione)
        movement_date = data_pag or data_em
        note_text = (row.note or "").strip()
        desc = f"Pagamento fattura ricevuta n. {row.numero} da {row.fornitore}"
        if note_text:
            desc += f" - {note_text}"

        session.execute(
            sa.text(
                "INSERT INTO erp_financial_movements "
                "(title, description, movement_type, movement_status, expense_type, category, "
                "amount, movement_date, month, year, source_type, source_id, created_at, updated_at) "
                "VALUES (:title, :desc, 'uscita', 'effettiva', 'variabile', 'fornitore', "
                ":amount, :movement_date, :month, :year, 'received_invoice', :source_id, "
                "DATETIME('now'), DATETIME('now'))"
            ),
            {
                "title": f"Pagamento fattura {row.numero} - {row.fornitore}",
                "desc": desc,
                "amount": float(row.importo) if row.importo is not None else 0,
                "movement_date": movement_date.isoformat() if movement_date else None,
                "month": movement_date.month if movement_date else None,
                "year": movement_date.year if movement_date else None,
                "source_id": row.id,
            },
        )

    session.commit()


def downgrade():
    bind = op.get_bind()
    session = Session(bind=bind)
    session.execute(
        sa.text(
            "DELETE FROM erp_financial_movements "
            "WHERE source_type = 'received_invoice'"
        )
    )
    session.commit()
