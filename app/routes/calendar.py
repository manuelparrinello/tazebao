from calendar import monthrange
from datetime import date, datetime, time, timedelta

from flask import Blueprint, redirect, render_template, request, url_for

from ..auth import login_required, role_required
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


def month_bounds(year, month):
    first_day = date(year, month, 1)
    last_day = date(year, month, monthrange(year, month)[1])
    next_month = last_day + timedelta(days=1)
    return first_day, last_day, next_month


def adjacent_month_urls(year, month):
    first_day = date(year, month, 1)
    prev_day = first_day - timedelta(days=1)
    next_day = month_bounds(year, month)[2]
    return (
        url_for("calendar.calendar_index", year=prev_day.year, month=prev_day.month),
        url_for("calendar.calendar_index", year=next_day.year, month=next_day.month),
    )


def calendar_event_item(event):
    return {
        "source": "calendar_event",
        "id": event.id,
        "title": event.title,
        "description": event.description,
        "event_type": event.event_type,
        "date": event.start_datetime.date(),
        "time": event.start_datetime.strftime("%H:%M"),
        "cliente": event.cliente,
        "lavoro": event.lavoro,
        "task": event.task,
        "assigned_user": event.assigned_user,
        "edit_url": url_for("calendar.calendar_edit", event_id=event.id),
    }


def task_due_date_item(task):
    return {
        "source": "task_due_date",
        "id": f"task-{task.id}",
        "title": task.name,
        "description": task.note,
        "event_type": "scadenza",
        "date": task.due_date,
        "time": None,
        "cliente": task.cliente,
        "lavoro": task.lavoro,
        "task": task,
        "assigned_user": task.assignee,
        "edit_url": url_for("tasks.task_edit", task_id=task.id),
    }


def build_month_weeks(year, month, items):
    first_day, last_day, _ = month_bounds(year, month)
    grid_start = first_day - timedelta(days=first_day.weekday())
    grid_end = last_day + timedelta(days=(6 - last_day.weekday()))
    items_by_date = {}

    for item in items:
        items_by_date.setdefault(item["date"], []).append(item)

    weeks = []
    current_day = grid_start
    while current_day <= grid_end:
        week = []
        for _ in range(7):
            day_events = sorted(
                items_by_date.get(current_day, []),
                key=lambda item: (item["time"] or "00:00", item["title"]),
            )
            week.append(
                {
                    "date": current_day,
                    "day": current_day.day,
                    "in_month": current_day.month == month,
                    "is_today": current_day == date.today(),
                    "events": day_events,
                }
            )
            current_day += timedelta(days=1)
        weeks.append(week)

    return weeks


@bp.get("/calendar")
@login_required
def calendar_index():
    today = date.today()
    current_year = request.args.get("year", today.year, type=int)
    current_month = request.args.get("month", today.month, type=int)

    if current_month < 1 or current_month > 12:
        current_year = today.year
        current_month = today.month

    first_day, last_day, next_month = month_bounds(current_year, current_month)
    range_start = datetime.combine(first_day, time.min)
    range_end = datetime.combine(next_month, time.min)

    events = (
        CalendarEvent.query.filter(CalendarEvent.start_datetime >= range_start)
        .filter(CalendarEvent.start_datetime < range_end)
        .order_by(CalendarEvent.start_datetime.asc())
        .all()
    )
    due_tasks = (
        Task.query.filter(Task.due_date >= first_day)
        .filter(Task.due_date <= last_day)
        .order_by(Task.due_date.asc(), Task.created_at.asc())
        .all()
    )

    calendar_items = [calendar_event_item(event) for event in events]
    calendar_items.extend(task_due_date_item(task) for task in due_tasks)
    calendar_items.sort(key=lambda item: (item["date"], item["time"] or "00:00", item["title"]))
    weeks = build_month_weeks(current_year, current_month, calendar_items)
    prev_month_url, next_month_url = adjacent_month_urls(current_year, current_month)

    return render_template(
        "calendar.html",
        events=calendar_items,
        event_types=CALENDAR_EVENT_TYPES,
        weeks=weeks,
        current_month=current_month,
        current_year=current_year,
        month_name=MONTH_NAMES[current_month],
        prev_month_url=prev_month_url,
        next_month_url=next_month_url,
    )


@bp.route("/calendar/new", methods=["GET", "POST"])
@role_required("admin", "operatore")
def calendar_new():
    lavoro_id = request.args.get("lavoro_id", type=int)
    cliente_id = request.args.get("cliente_id", type=int)
    lavoro = Lavoro.query.get(lavoro_id) if lavoro_id else None
    if lavoro_id and not lavoro:
        lavoro_id = None
    if lavoro and not cliente_id:
        cliente_id = lavoro.cliente_id
    event = CalendarEvent(cliente_id=cliente_id, lavoro_id=lavoro_id)
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
@role_required("admin", "operatore")
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
@role_required("admin", "operatore")
def calendar_delete(event_id):
    event = CalendarEvent.query.get_or_404(event_id)
    db.session.delete(event)
    db.session.commit()
    return redirect(url_for("calendar.calendar_index"))
