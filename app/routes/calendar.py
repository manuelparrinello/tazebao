from datetime import datetime

from flask import Blueprint, redirect, render_template, request, url_for

from ..auth import login_required
from ..extensions import db
from ..models import (
    CALENDAR_EVENT_TYPES,
    CalendarEvent,
    Cliente,
    Lavoro,
    Task,
    User,
)


bp = Blueprint("calendar", __name__)


def parse_optional_datetime(value):
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%dT%H:%M")


def parse_optional_id(value):
    if not value:
        return None
    return int(value)


def calendar_form_choices():
    return {
        "event_types": CALENDAR_EVENT_TYPES,
        "clienti": Cliente.query.order_by(Cliente.name.asc()).all(),
        "lavori": Lavoro.query.order_by(Lavoro.descrizione.asc()).all(),
        "tasks": Task.query.order_by(Task.created_at.desc()).all(),
        "users": User.query.order_by(User.name.asc(), User.email.asc()).all(),
    }


def apply_calendar_form(event):
    event.title = (request.form.get("title") or "").strip()
    event.description = (request.form.get("description") or "").strip() or None
    event.event_type = request.form.get("event_type") or "generale"
    event.start_datetime = parse_optional_datetime(request.form.get("start_datetime"))
    event.end_datetime = parse_optional_datetime(request.form.get("end_datetime"))
    event.cliente_id = parse_optional_id(request.form.get("cliente_id"))
    event.lavoro_id = parse_optional_id(request.form.get("lavoro_id"))
    event.task_id = parse_optional_id(request.form.get("task_id"))
    event.assigned_user_id = parse_optional_id(request.form.get("assigned_user_id"))

    if not event.title:
        raise ValueError("Il titolo evento e obbligatorio.")
    if event.event_type not in CALENDAR_EVENT_TYPES:
        raise ValueError("Tipo evento non valido.")
    if event.start_datetime is None:
        raise ValueError("La data inizio evento e obbligatoria.")
    if event.end_datetime and event.end_datetime < event.start_datetime:
        raise ValueError("La data fine non puo precedere la data inizio.")


@bp.get("/calendar")
@login_required
def calendar_index():
    events = CalendarEvent.query.order_by(CalendarEvent.start_datetime.asc()).all()
    return render_template(
        "calendar.html",
        events=events,
        event_types=CALENDAR_EVENT_TYPES,
    )


@bp.route("/calendar/new", methods=["GET", "POST"])
@login_required
def calendar_new():
    event = CalendarEvent()
    error = None

    if request.method == "POST":
        try:
            apply_calendar_form(event)
            db.session.add(event)
            db.session.commit()
            return redirect(url_for("calendar.calendar_index"))
        except ValueError as exc:
            db.session.rollback()
            error = str(exc)

    return render_template(
        "calendar_event_form.html",
        event=event,
        error=error,
        form_action=url_for("calendar.calendar_new"),
        page_title="Nuovo evento",
        submit_label="Crea evento",
        **calendar_form_choices(),
    )


@bp.route("/calendar/<int:event_id>/edit", methods=["GET", "POST"])
@login_required
def calendar_edit(event_id):
    event = CalendarEvent.query.get_or_404(event_id)
    error = None

    if request.method == "POST":
        try:
            apply_calendar_form(event)
            db.session.commit()
            return redirect(url_for("calendar.calendar_index"))
        except ValueError as exc:
            db.session.rollback()
            error = str(exc)

    return render_template(
        "calendar_event_form.html",
        event=event,
        error=error,
        form_action=url_for("calendar.calendar_edit", event_id=event.id),
        page_title="Modifica evento",
        submit_label="Salva modifiche",
        **calendar_form_choices(),
    )


@bp.post("/calendar/<int:event_id>/delete")
@login_required
def calendar_delete(event_id):
    event = CalendarEvent.query.get_or_404(event_id)
    db.session.delete(event)
    db.session.commit()
    return redirect(url_for("calendar.calendar_index"))
