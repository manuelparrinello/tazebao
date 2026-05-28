from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import func

from .extensions import db
from .models import (
    FINANCE_CATEGORIES,
    FINANCE_EXPENSE_TYPES,
    FINANCE_MOVEMENT_STATUSES,
    FINANCE_MOVEMENT_TYPES,
    Cliente,
    FinancialMovement,
    Lavoro,
)


from .utils.calendar_helpers import MONTH_NAMES


def parse_finance_date(value):
    if isinstance(value, date):
        return value
    if not value:
        raise ValueError("La data movimento e obbligatoria.")
    return datetime.strptime(value, "%Y-%m-%d").date()


def parse_finance_amount(value):
    if value in (None, ""):
        raise ValueError("L'importo e obbligatorio.")
    return Decimal(str(value).replace(",", "."))


from .utils.parsing import parse_optional_id


def normalize_financial_movement(movement):
    if movement.movement_type not in FINANCE_MOVEMENT_TYPES:
        raise ValueError("Tipo movimento non valido.")
    if movement.category not in FINANCE_CATEGORIES:
        raise ValueError("Categoria movimento non valida.")
    if movement.amount < 0:
        raise ValueError("L'importo non puo essere negativo.")

    movement.month = movement.movement_date.month
    movement.year = movement.movement_date.year

    if movement.movement_type == "entrata":
        if movement.movement_status not in FINANCE_MOVEMENT_STATUSES:
            raise ValueError("Stato entrata non valido.")
        movement.expense_type = None
    else:
        movement.movement_status = "effettiva"
        if movement.expense_type not in FINANCE_EXPENSE_TYPES:
            raise ValueError("Tipo uscita non valido.")


def apply_financial_payload(movement, data, partial=False, created_by=None):
    if not partial or "title" in data:
        movement.title = (data.get("title") or "").strip()
    if not partial or "description" in data:
        movement.description = (data.get("description") or "").strip() or None
    if not partial or "movement_type" in data:
        movement.movement_type = data.get("movement_type") or "uscita"
    if not partial or "movement_status" in data:
        movement.movement_status = data.get("movement_status") or "prevista"
    if not partial or "expense_type" in data:
        movement.expense_type = data.get("expense_type") or None
    if not partial or "category" in data:
        movement.category = data.get("category") or "generale"
    if not partial or "amount" in data:
        movement.amount = parse_finance_amount(data.get("amount"))
    if not partial or "movement_date" in data:
        movement.movement_date = parse_finance_date(data.get("movement_date"))
    if not partial or "cliente_id" in data:
        movement.cliente_id = parse_optional_id(data.get("cliente_id"))
    if not partial or "lavoro_id" in data:
        movement.lavoro_id = parse_optional_id(data.get("lavoro_id"))

    if created_by and movement.created_by is None:
        movement.created_by = created_by

    if not movement.title:
        raise ValueError("Il titolo movimento e obbligatorio.")
    if movement.movement_date is None:
        raise ValueError("La data movimento e obbligatoria.")

    normalize_financial_movement(movement)


def finance_summary(year=None, month=None):
    today = date.today()
    year = year or today.year
    month = month or today.month

    movements = FinancialMovement.query.all()
    month_movements = [
        movement
        for movement in movements
        if movement.year == year and movement.month == month
    ]

    total_income_effective_all = sum(
        movement.amount
        for movement in movements
        if movement.movement_type == "entrata"
        and movement.movement_status == "effettiva"
    )
    total_expenses_all = sum(
        movement.amount for movement in movements if movement.movement_type == "uscita"
    )

    month_income_expected = sum(
        movement.amount
        for movement in month_movements
        if movement.movement_type == "entrata"
        and movement.movement_status == "prevista"
    )
    month_income_effective = sum(
        movement.amount
        for movement in month_movements
        if movement.movement_type == "entrata"
        and movement.movement_status == "effettiva"
    )
    month_expenses_fixed = sum(
        movement.amount
        for movement in month_movements
        if movement.movement_type == "uscita" and movement.expense_type == "fissa"
    )
    month_expenses_variable = sum(
        movement.amount
        for movement in month_movements
        if movement.movement_type == "uscita" and movement.expense_type == "variabile"
    )
    month_expenses_total = month_expenses_fixed + month_expenses_variable
    month_balance = month_income_effective - month_expenses_total
    current_balance = total_income_effective_all - total_expenses_all

    return {
        "year": year,
        "month": month,
        "month_name": MONTH_NAMES[month],
        "current_balance": float(current_balance),
        "month_income_effective": float(month_income_effective),
        "month_income_expected": float(month_income_expected),
        "month_income_total": float(month_income_effective + month_income_expected),
        "month_expenses_fixed": float(month_expenses_fixed),
        "month_expenses_variable": float(month_expenses_variable),
        "month_expenses_total": float(month_expenses_total),
        "month_balance": float(month_balance),
    }


def delete_financial_movement(movement):
    db.session.delete(movement)


def invoice_gross_amount(invoice):
    """Calcola il totale lordo IVA inclusa di una fattura.

    Fattura.importo e' l'imponibile (IVA esclusa) inserito dall'utente.
    Il lordo e' usato per i movimenti finance per rappresentare
    il cash flow reale dell'azienda.

    Formula: importo * (1 + aliquota_iva / 100)
    """
    net = Decimal(str(invoice.importo or 0))
    iva = Decimal(str(invoice.aliquota_iva or 0))
    return (net * (Decimal(1) + iva / Decimal(100))).quantize(Decimal("0.01"))


def sync_movement_from_received_invoice(invoice):
    """Create, update, or remove FinancialMovement linked to a received invoice.

    Called after invoice save/update when invoice_type == 'received'.
    Handles all three cases:
    - invoice paid (stato_pagamento == 'pagata') → create or update movement
    - invoice not paid → remove linked movement if auto-generated
    """
    from datetime import date as dt_date

    if invoice.invoice_type != "received":
        return

    existing = FinancialMovement.query.filter_by(
        source_type="received_invoice",
        source_id=invoice.id,
    ).first()

    if invoice.stato_pagamento == "pagata":
        if existing:
            _update_movement_from_invoice(existing, invoice)
        else:
            _create_movement_from_invoice(invoice)
    else:
        if existing:
            db.session.delete(existing)


def _create_movement_from_invoice(invoice):
    movement_date = invoice.data_pagamento or invoice.data_emissione
    movement = FinancialMovement(
        title=f"Pagamento fattura {invoice.numero} - {invoice.fornitore}",
        description=(
            f"Pagamento fattura ricevuta n. {invoice.numero} "
            f"da {invoice.fornitore} "
            f"- {invoice.note or ''}"
        ).strip("- ").strip(),
        movement_type="uscita",
        movement_status="effettiva",
        expense_type="variabile",
        category="fornitore",
        amount=float(invoice_gross_amount(invoice)),
        movement_date=movement_date,
        month=movement_date.month,
        year=movement_date.year,
        source_type="received_invoice",
        source_id=invoice.id,
    )
    db.session.add(movement)


def _update_movement_from_invoice(movement, invoice):
    movement.title = f"Pagamento fattura {invoice.numero} - {invoice.fornitore}"
    movement.description = (
        f"Pagamento fattura ricevuta n. {invoice.numero} "
        f"da {invoice.fornitore} "
        f"- {invoice.note or ''}"
    ).strip("- ").strip()
    movement.amount = float(invoice_gross_amount(invoice))
    movement.movement_date = invoice.data_pagamento or invoice.data_emissione
    movement.month = movement.movement_date.month
    movement.year = movement.movement_date.year
    movement.category = "fornitore"
    movement.expense_type = "variabile"


def sync_movement_from_sent_invoice(invoice):
    """Create, update, or remove FinancialMovement linked to a sent invoice.

    Called after invoice save/update when invoice_type == 'sent'.
    Handles all three cases:
    - invoice paid (pagato == True) -> create or update movement
    - invoice not paid -> remove linked movement if auto-generated
    """
    if invoice.invoice_type != "sent":
        return

    existing = FinancialMovement.query.filter_by(
        source_type="sent_invoice",
        source_id=invoice.id,
    ).first()

    if invoice.pagato:
        if existing:
            _update_movement_from_sent_invoice(existing, invoice)
        else:
            _create_movement_from_sent_invoice(invoice)
    else:
        if existing:
            db.session.delete(existing)


def _create_movement_from_sent_invoice(invoice):
    movement_date = invoice.data_pagamento or invoice.data_emissione
    cliente_name = invoice.cliente.name if invoice.cliente else ""
    movement = FinancialMovement(
        title=f"Pagamento fattura cliente n. {invoice.numero} - {cliente_name}",
        description=(
            f"Pagamento fattura cliente n. {invoice.numero} "
            f"- {cliente_name} "
            f"- {invoice.note or ''}"
        ).strip("- ").strip(),
        movement_type="entrata",
        movement_status="effettiva",
        category="pagamento_cliente",
        amount=float(invoice_gross_amount(invoice)),
        movement_date=movement_date,
        month=movement_date.month,
        year=movement_date.year,
        cliente_id=invoice.cliente_id,
        lavoro_id=invoice.lavoro_id,
        source_type="sent_invoice",
        source_id=invoice.id,
    )
    db.session.add(movement)


def _update_movement_from_sent_invoice(movement, invoice):
    cliente_name = invoice.cliente.name if invoice.cliente else ""
    movement.title = f"Pagamento fattura cliente n. {invoice.numero} - {cliente_name}"
    movement.description = (
        f"Pagamento fattura cliente n. {invoice.numero} "
        f"- {cliente_name} "
        f"- {invoice.note or ''}"
    ).strip("- ").strip()
    movement.amount = float(invoice_gross_amount(invoice))
    movement.movement_date = invoice.data_pagamento or invoice.data_emissione
    movement.month = movement.movement_date.month
    movement.year = movement.movement_date.year
    movement.cliente_id = invoice.cliente_id
    movement.lavoro_id = invoice.lavoro_id
    movement.category = "pagamento_cliente"


# I movimenti finance utilizzano importi IVA inclusa (lordi) per
# rappresentare il cash flow reale. Le funzioni di marginalita' che seguono
# leggono anch'esse da FinancialMovement.amount pertanto riflettono i valori
# lordi. L'IVA non rappresenta un ricavo o un costo aziendale ma un flusso
# fiscale separato; nel contesto della marginalita' i valori lordi sono
# accettati perche' il sistema e' orientato al cash flow reale.


def cliente_marginality(cliente_id):
    income = (
        db.session.query(func.coalesce(func.sum(FinancialMovement.amount), 0))
        .filter(
            FinancialMovement.cliente_id == cliente_id,
            FinancialMovement.movement_type == "entrata",
            FinancialMovement.movement_status == "effettiva",
        )
        .scalar()
    )
    expenses = (
        db.session.query(func.coalesce(func.sum(FinancialMovement.amount), 0))
        .filter(
            FinancialMovement.cliente_id == cliente_id,
            FinancialMovement.movement_type == "uscita",
        )
        .scalar()
    )
    count = (
        db.session.query(func.count(FinancialMovement.id))
        .filter(FinancialMovement.cliente_id == cliente_id)
        .scalar()
    )
    last = (
        db.session.query(func.max(FinancialMovement.movement_date))
        .filter(FinancialMovement.cliente_id == cliente_id)
        .scalar()
    )
    return {
        "total_income": float(income),
        "total_expenses": float(expenses),
        "net": float(income - expenses),
        "movement_count": count,
        "last_movement_date": last.isoformat() if last else None,
    }


def lavoro_marginality(lavoro_id):
    income = (
        db.session.query(func.coalesce(func.sum(FinancialMovement.amount), 0))
        .filter(
            FinancialMovement.lavoro_id == lavoro_id,
            FinancialMovement.movement_type == "entrata",
            FinancialMovement.movement_status == "effettiva",
        )
        .scalar()
    )
    expenses = (
        db.session.query(func.coalesce(func.sum(FinancialMovement.amount), 0))
        .filter(
            FinancialMovement.lavoro_id == lavoro_id,
            FinancialMovement.movement_type == "uscita",
        )
        .scalar()
    )
    return {
        "total_income": float(income),
        "total_expenses": float(expenses),
        "net": float(income - expenses),
    }


def _client_margin_rows(limit=5):
    rows = (
        db.session.query(
            Cliente.id,
            Cliente.name,
            func.coalesce(func.sum(FinancialMovement.amount), 0).label("income"),
        )
        .join(FinancialMovement, FinancialMovement.cliente_id == Cliente.id)
        .filter(
            FinancialMovement.movement_type == "entrata",
            FinancialMovement.movement_status == "effettiva",
        )
        .group_by(Cliente.id, Cliente.name)
        .order_by(func.sum(FinancialMovement.amount).desc())
        .limit(limit)
        .all()
    )
    result = []
    for r in rows:
        expenses = (
            db.session.query(func.coalesce(func.sum(FinancialMovement.amount), 0))
            .filter(
                FinancialMovement.cliente_id == r.id,
                FinancialMovement.movement_type == "uscita",
            )
            .scalar()
        )
        result.append(
            {
                "id": r.id,
                "name": r.name,
                "income": float(r.income),
                "expenses": float(expenses),
                "net": float(r.income - expenses),
            }
        )
    return result


def _job_margin_rows(limit=5):
    rows = (
        db.session.query(
            Lavoro.id,
            Lavoro.descrizione,
            Lavoro.cliente_id,
            func.coalesce(Lavoro.preventivato, 0).label("preventivato"),
        )
        .filter(Lavoro.preventivato.isnot(None), Lavoro.preventivato > 0)
        .limit(limit)
        .all()
    )
    result = []
    for r in rows:
        income = (
            db.session.query(func.coalesce(func.sum(FinancialMovement.amount), 0))
            .filter(
                FinancialMovement.lavoro_id == r.id,
                FinancialMovement.movement_type == "entrata",
                FinancialMovement.movement_status == "effettiva",
            )
            .scalar()
        )
        expenses = (
            db.session.query(func.coalesce(func.sum(FinancialMovement.amount), 0))
            .filter(
                FinancialMovement.lavoro_id == r.id,
                FinancialMovement.movement_type == "uscita",
            )
            .scalar()
        )
        cliente_name = ""
        if r.cliente_id:
            c = db.session.get(Cliente, r.cliente_id)
            if c:
                cliente_name = c.name
        result.append(
            {
                "id": r.id,
                "descrizione": r.descrizione,
                "cliente_name": cliente_name,
                "preventivato": float(r.preventivato),
                "income": float(income),
                "expenses": float(expenses),
                "net": float(income - expenses),
            }
        )
    return result


def _losing_jobs(limit=5):
    rows = (
        db.session.query(
            Lavoro.id,
            Lavoro.descrizione,
            Lavoro.cliente_id,
        )
        .all()
    )
    result = []
    for r in rows:
        income = (
            db.session.query(func.coalesce(func.sum(FinancialMovement.amount), 0))
            .filter(
                FinancialMovement.lavoro_id == r.id,
                FinancialMovement.movement_type == "entrata",
                FinancialMovement.movement_status == "effettiva",
            )
            .scalar()
        )
        expenses = (
            db.session.query(func.coalesce(func.sum(FinancialMovement.amount), 0))
            .filter(
                FinancialMovement.lavoro_id == r.id,
                FinancialMovement.movement_type == "uscita",
            )
            .scalar()
        )
        net = income - expenses
        if net < 0:
            cliente_name = ""
            if r.cliente_id:
                c = db.session.get(Cliente, r.cliente_id)
                if c:
                    cliente_name = c.name
            result.append(
                {
                    "id": r.id,
                    "descrizione": r.descrizione,
                    "cliente_name": cliente_name,
                    "income": float(income),
                    "expenses": float(expenses),
                    "net": float(net),
                }
            )
    result.sort(key=lambda x: x["net"])
    return result[:limit]


def marginality_ranking():
    return {
        "top_clients": _client_margin_rows(5),
        "top_jobs": _job_margin_rows(5),
        "losing_jobs": _losing_jobs(5),
    }
