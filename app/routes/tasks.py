from datetime import datetime

from flask import Blueprint, redirect, render_template, request, url_for

from ..auth import login_required
from ..extensions import db
from ..models import (
    TASK_CATEGORIES,
    TASK_PRIORITIES,
    TASK_STATUSES,
    Cliente,
    Lavoro,
    Task,
    User,
)


bp = Blueprint("tasks", __name__)


def parse_optional_date(value):
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%d").date()


def parse_optional_id(value):
    if not value:
        return None
    return int(value)


def task_form_choices():
    return {
        "categories": TASK_CATEGORIES,
        "statuses": TASK_STATUSES,
        "priorities": TASK_PRIORITIES,
        "clienti": Cliente.query.order_by(Cliente.name.asc()).all(),
        "lavori": Lavoro.query.order_by(Lavoro.descrizione.asc()).all(),
        "users": User.query.order_by(User.name.asc(), User.email.asc()).all(),
    }


def apply_task_form(task):
    task.name = (request.form.get("name") or "").strip()
    task.note = (request.form.get("note") or "").strip() or None
    task.category = request.form.get("category") or "generale"
    task.status = request.form.get("status") or "da_fare"
    task.priority = request.form.get("priority") or "media"
    task.due_date = parse_optional_date(request.form.get("due_date"))
    task.cliente_id = parse_optional_id(request.form.get("cliente_id"))
    task.lavoro_id = parse_optional_id(request.form.get("lavoro_id"))
    task.assignee_id = parse_optional_id(request.form.get("assignee_id"))

    if not task.name:
        raise ValueError("Il titolo task e obbligatorio.")
    if task.category not in TASK_CATEGORIES:
        raise ValueError("Categoria task non valida.")
    if task.status not in TASK_STATUSES:
        raise ValueError("Stato task non valido.")
    if task.priority not in TASK_PRIORITIES:
        raise ValueError("Priorita task non valida.")


@bp.get("/tasks")
@login_required
def tasks():
    tasks_list = Task.query.order_by(Task.created_at.desc()).all()
    return render_template(
        "tasks.html",
        tasks=tasks_list,
        categories=TASK_CATEGORIES,
        statuses=TASK_STATUSES,
        priorities=TASK_PRIORITIES,
    )


@bp.route("/tasks/new", methods=["GET", "POST"])
@login_required
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
@login_required
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
@login_required
def task_delete(task_id):
    task = Task.query.get_or_404(task_id)
    task.status = "annullata"
    db.session.commit()
    return redirect(url_for("tasks.tasks"))
