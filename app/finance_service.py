from datetime import date, datetime
from decimal import Decimal

from .extensions import db
from .models import (
    FINANCE_CATEGORIES,
    FINANCE_EXPENSE_TYPES,
    FINANCE_MOVEMENT_STATUSES,
    FINANCE_MOVEMENT_TYPES,
    FinancialMovement,
)


MONTH_NAMES = (
    "",
    "Gennaio",
    "Febbraio",
    "Marzo",
    "Aprile",
    "Maggio",
    "Giugno",
    "Luglio",
    "Agosto",
    "Settembre",
    "Ottobre",
    "Novembre",
    "Dicembre",
)


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


def parse_optional_id(value):
    if value in (None, ""):
        return None
    return int(value)


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
