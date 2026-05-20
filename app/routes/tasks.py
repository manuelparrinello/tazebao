from datetime import date, timedelta

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for

from ..auth import login_required, role_required
from ..extensions import db
from ..models import (
    TASK_CATEGORIES,
    TASK_PRIORITIES,
    TASK_STATUSES,
    CalendarEvent,
    Cliente,
    EmailLog,
    Lavoro,
    Task,
)
from ..utils.parsing import parse_optional_date, parse_optional_id


bp = Blueprint("tasks", __name__)


def task_form_choices():
    return {
        "categories": TASK_CATEGORIES,
        "statuses": TASK_STATUSES,
        "priorities": TASK_PRIORITIES,
        "clienti": Cliente.query.order_by(Cliente.name.asc()).all(),
        "lavori": Lavoro.query.order_by(Lavoro.descrizione.asc()).all(),
    }


def validate_fk_id(model, id_value, label):
    if id_value is not None:
        obj = db.session.get(model, id_value)
        if obj is None:
            raise ValueError(f"{label} con ID {id_value} non trovato.")
    return id_value

def apply_task_form(task):
    task.name = (request.form.get("name") or "").strip()
    task.note = (request.form.get("note") or "").strip() or None
    task.category = request.form.get("category") or "generale"
    task.status = request.form.get("status") or "da_fare"
    task.priority = request.form.get("priority") or "media"
    task.due_date = parse_optional_date(request.form.get("due_date"))
    task.cliente_id = validate_fk_id(Cliente, parse_optional_id(request.form.get("cliente_id")), "Cliente")
    task.lavoro_id = validate_fk_id(Lavoro, parse_optional_id(request.form.get("lavoro_id")), "Lavoro")
    if not task.name:
        raise ValueError("Il titolo task e obbligatorio.")
    if task.category not in TASK_CATEGORIES:
        raise ValueError("Categoria task non valida.")
    if task.status not in TASK_STATUSES:
        raise ValueError("Stato task non valido.")
    if task.priority not in TASK_PRIORITIES:
        raise ValueError("Priorita task non valida.")


TASK_FILTERS = {"aperte", "scadute", "in_scadenza", "urgenti"}
CLOSED_STATUSES = ("completata", "annullata")


@bp.get("/tasks")
@login_required
def tasks():
    filter_name = request.args.get("filter", "").strip().lower()
    if filter_name not in TASK_FILTERS:
        filter_name = None

    query = Task.query
    today = date.today()

    if filter_name == "aperte":
        query = query.filter(~Task.status.in_(CLOSED_STATUSES))
    elif filter_name == "scadute":
        query = query.filter(
            Task.due_date < today,
            ~Task.status.in_(CLOSED_STATUSES),
        )
    elif filter_name == "in_scadenza":
        query = query.filter(
            Task.due_date >= today,
            Task.due_date <= today + timedelta(days=3),
            ~Task.status.in_(CLOSED_STATUSES),
        )
    elif filter_name == "urgenti":
        query = query.filter(
            Task.priority.in_(("alta", "urgente")),
            ~Task.status.in_(CLOSED_STATUSES),
        )

    tasks_list = query.order_by(Task.created_at.desc()).all()
    return render_template(
        "tasks.html",
        tasks=tasks_list,
        categories=TASK_CATEGORIES,
        statuses=TASK_STATUSES,
        priorities=TASK_PRIORITIES,
        active_filter=filter_name,
    )


@bp.route("/tasks/new", methods=["GET", "POST"])
@role_required("admin", "operatore")
def task_new():
    lavoro_id = request.args.get("lavoro_id", type=int)
    cliente_id = request.args.get("cliente_id", type=int)
    lavoro = Lavoro.query.get(lavoro_id) if lavoro_id else None
    if lavoro_id and not lavoro:
        lavoro_id = None
    if lavoro and not cliente_id:
        cliente_id = lavoro.cliente_id
    task = Task(cliente_id=cliente_id, lavoro_id=lavoro_id)
    error = None

    if request.method == "POST":
        try:
            apply_task_form(task)
            db.session.add(task)
            db.session.commit()
            return redirect(url_for("tasks.tasks"))
        except ValueError as exc:
            db.session.rollback()
            error = str(exc)

    return render_template(
        "task_form.html",
        task=task,
        error=error,
        form_action=url_for("tasks.task_new"),
        page_title="Nuovo task",
        submit_label="Crea task",
        **task_form_choices(),
    )


@bp.route("/tasks/<int:task_id>/edit", methods=["GET", "POST"])
@role_required("admin", "operatore")
def task_edit(task_id):
    task = Task.query.get_or_404(task_id)
    error = None

    if request.method == "POST":
        try:
            apply_task_form(task)
            db.session.commit()
            return redirect(url_for("tasks.tasks"))
        except ValueError as exc:
            db.session.rollback()
            error = str(exc)

    return render_template(
        "task_form.html",
        task=task,
        error=error,
        form_action=url_for("tasks.task_edit", task_id=task.id),
        page_title="Modifica task",
        submit_label="Salva modifiche",
        **task_form_choices(),
    )


@bp.post("/tasks/<int:task_id>/delete")
@role_required("admin", "operatore")
def task_delete(task_id):
    task = Task.query.get_or_404(task_id)
    try:
        for moodboard in task.moodboards:
            moodboard.task_id = None
        CalendarEvent.query.filter_by(task_id=task_id).update({CalendarEvent.task_id: None})
        EmailLog.query.filter_by(task_id=task_id).update({EmailLog.task_id: None})
        db.session.delete(task)
        db.session.commit()
        flash("Task eliminata con successo.", "success")
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Errore eliminazione task %d", task_id)
        flash("Impossibile eliminare il task. Operazione annullata.", "danger")
    return redirect(url_for("tasks.tasks"))
