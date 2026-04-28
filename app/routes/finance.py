from datetime import date

from flask import Blueprint, g, redirect, render_template, request, url_for

from ..auth import login_required
from ..extensions import db
from ..finance_service import (
    MONTH_NAMES,
    apply_financial_payload,
    delete_financial_movement,
    finance_summary,
)
from ..models import (
    FINANCE_CATEGORIES,
    FINANCE_EXPENSE_TYPES,
    FINANCE_MOVEMENT_STATUSES,
    FINANCE_MOVEMENT_TYPES,
    Cliente,
    FinancialMovement,
    Lavoro,
)


bp = Blueprint("finance", __name__)


def finance_form_choices():
    return {
        "movement_types": FINANCE_MOVEMENT_TYPES,
        "movement_statuses": FINANCE_MOVEMENT_STATUSES,
        "expense_types": FINANCE_EXPENSE_TYPES,
        "categories": FINANCE_CATEGORIES,
        "clienti": Cliente.query.order_by(Cliente.name.asc()).all(),
        "lavori": Lavoro.query.order_by(Lavoro.descrizione.asc()).all(),
    }


@bp.get("/finance")
@login_required
def finance_index():
    today = date.today()
    year = request.args.get("year", today.year, type=int)
    month = request.args.get("month", today.month, type=int)

    if month < 1 or month > 12:
        year = today.year
        month = today.month

    summary = finance_summary(year, month)
    movements = (
        FinancialMovement.query.filter_by(year=year, month=month)
        .order_by(FinancialMovement.movement_date.asc(), FinancialMovement.id.asc())
        .all()
    )
    income_movements = [m for m in movements if m.movement_type == "entrata"]
    expense_movements = [m for m in movements if m.movement_type == "uscita"]

    return render_template(
        "finance.html",
        summary=summary,
        income_movements=income_movements,
        expense_movements=expense_movements,
        current_year=year,
        current_month=month,
        months=enumerate(MONTH_NAMES),
    )


@bp.route("/finance/new", methods=["GET", "POST"])
@login_required
def finance_new():
    movement = FinancialMovement(
        movement_date=date.today(),
        cliente_id=request.args.get("cliente_id", type=int),
    )
    error = None

    if request.method == "POST":
        try:
            created_by = g.current_user.id if g.get("current_user") else None
            apply_financial_payload(movement, request.form, created_by=created_by)
            db.session.add(movement)
            db.session.commit()
            return redirect(
                url_for("finance.finance_index", year=movement.year, month=movement.month)
            )
        except ValueError as exc:
            db.session.rollback()
            error = str(exc)

    return render_template(
        "finance_form.html",
        movement=movement,
        error=error,
        form_action=url_for("finance.finance_new"),
        page_title="Nuovo movimento",
        submit_label="Crea movimento",
        **finance_form_choices(),
    )


@bp.route("/finance/<int:movement_id>/edit", methods=["GET", "POST"])
@login_required
def finance_edit(movement_id):
    movement = FinancialMovement.query.get_or_404(movement_id)
    error = None

    if request.method == "POST":
        try:
            apply_financial_payload(movement, request.form, partial=True)
            db.session.commit()
            return redirect(
                url_for("finance.finance_index", year=movement.year, month=movement.month)
            )
        except ValueError as exc:
            db.session.rollback()
            error = str(exc)

    return render_template(
        "finance_form.html",
        movement=movement,
        error=error,
        form_action=url_for("finance.finance_edit", movement_id=movement.id),
        page_title="Modifica movimento",
        submit_label="Salva modifiche",
        **finance_form_choices(),
    )


@bp.post("/finance/<int:movement_id>/delete")
@login_required
def finance_delete(movement_id):
    movement = FinancialMovement.query.get_or_404(movement_id)
    year = movement.year
    month = movement.month
    delete_financial_movement(movement)
    db.session.commit()
    return redirect(url_for("finance.finance_index", year=year, month=month))
