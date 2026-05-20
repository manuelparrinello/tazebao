from datetime import date, datetime, time, timedelta

from flask import Blueprint, g, request, url_for

from ..auth import login_required, role_required
from ..extensions import db
from ..finance_service import (
    apply_financial_payload,
    delete_financial_movement,
    finance_summary,
)
from ..models import (
    CalendarEvent,
    Cliente,
    EditorialPublication,
    EmailLog,
    EmailMessage,
    FinancialMovement,
    Lavoro,
    Preventivo,
)
from ..models import (
    CALENDAR_EVENT_TYPES,
    EMAIL_DIRECTIONS,
    TASK_CATEGORIES,
    TASK_PRIORITIES,
    TASK_STATUSES,
    Task,
)
from ..utils.api import api_response
from ..utils.parsing import parse_optional_date, parse_optional_datetime, parse_optional_id


bp = Blueprint("api", __name__)


def apply_calendar_payload(event, data, partial=False):
    if not partial or "title" in data:
        event.title = (data.get("title") or "").strip()
    if not partial or "description" in data:
        event.description = (data.get("description") or "").strip() or None
    if not partial or "event_type" in data:
        event.event_type = data.get("event_type") or "generale"
    if not partial or "start_datetime" in data:
        event.start_datetime = parse_optional_datetime(data.get("start_datetime"))
    if not partial or "end_datetime" in data:
        event.end_datetime = parse_optional_datetime(data.get("end_datetime"))
    if not partial or "cliente_id" in data:
        event.cliente_id = parse_optional_id(data.get("cliente_id"))
    if not partial or "lavoro_id" in data:
        event.lavoro_id = parse_optional_id(data.get("lavoro_id"))
    if not partial or "task_id" in data:
        event.task_id = parse_optional_id(data.get("task_id"))

    if not event.title:
        raise ValueError("Il titolo evento e obbligatorio.")
    if event.event_type not in CALENDAR_EVENT_TYPES:
        raise ValueError("Tipo evento non valido.")
    if event.start_datetime is None:
        raise ValueError("La data inizio evento e obbligatoria.")
    if event.end_datetime and event.end_datetime < event.start_datetime:
        raise ValueError("La data fine non puo precedere la data inizio.")


def apply_email_payload(email_log, data, partial=False):
    if not partial or "subject" in data:
        email_log.subject = (data.get("subject") or "").strip()
    if not partial or "body" in data:
        email_log.body = (data.get("body") or "").strip() or None
    if not partial or "direction" in data:
        email_log.direction = data.get("direction") or "outbound"
    if not partial or "email_address" in data:
        email_log.email_address = (data.get("email_address") or "").strip().lower()
    if not partial or "cliente_id" in data:
        email_log.cliente_id = parse_optional_id(data.get("cliente_id"))
    if not partial or "lavoro_id" in data:
        email_log.lavoro_id = parse_optional_id(data.get("lavoro_id"))
    if not partial or "task_id" in data:
        email_log.task_id = parse_optional_id(data.get("task_id"))
    if not partial or "sent_at" in data:
        email_log.sent_at = parse_optional_datetime(data.get("sent_at"))
    if not partial or "message_id" in data:
        email_log.message_id = (data.get("message_id") or "").strip() or None
    if not partial or "thread_id" in data:
        email_log.thread_id = (data.get("thread_id") or "").strip() or None
    if not partial or "provider" in data:
        email_log.provider = (data.get("provider") or "").strip() or None
    if not partial or "provider_account" in data:
        email_log.provider_account = (data.get("provider_account") or "").strip() or None

    if not email_log.subject:
        raise ValueError("L'oggetto e obbligatorio.")
    if email_log.direction not in EMAIL_DIRECTIONS:
        raise ValueError("Direzione comunicazione non valida.")
    if not email_log.email_address:
        raise ValueError("L'indirizzo email e obbligatorio.")
    if email_log.sent_at is None:
        raise ValueError("La data comunicazione e obbligatoria.")


def task_due_date_to_calendar_event(task):
    start_datetime = datetime.combine(task.due_date, time.min)
    return {
        "source": "task_due_date",
        "id": f"task-{task.id}",
        "title": f"Scadenza task: {task.name}",
        "description": task.note,
        "event_type": "scadenza",
        "start_datetime": start_datetime.isoformat(),
        "end_datetime": None,
        "cliente_id": task.cliente_id,
        "cliente": (
            {"id": task.cliente.id, "name": task.cliente.name}
            if task.cliente
            else None
        ),
        "lavoro_id": task.lavoro_id,
        "lavoro": (
            {"id": task.lavoro.id, "descrizione": task.lavoro.descrizione}
            if task.lavoro
            else None
        ),
        "task_id": task.id,
        "task": task.to_dict(),
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "updated_at": task.updated_at.isoformat() if task.updated_at else None,
    }


def serialize_dashboard_task(task):
    return {
        "id": task.id,
        "url": url_for("tasks.task_edit", task_id=task.id),
        "name": task.name,
        "status": task.status,
        "priority": task.priority,
        "due_date": task.due_date.isoformat() if task.due_date else None,
        "cliente": (
            {"id": task.cliente.id, "name": task.cliente.name}
            if task.cliente
            else None
        ),
        "lavoro": (
            {"id": task.lavoro.id, "descrizione": task.lavoro.descrizione}
            if task.lavoro
            else None
        ),
    }


def serialize_dashboard_event(event):
    return {
        "id": event.id,
        "url": url_for("calendar.calendar_edit", event_id=event.id),
        "title": event.title,
        "event_type": event.event_type,
        "start_datetime": (
            event.start_datetime.isoformat() if event.start_datetime else None
        ),
        "cliente": (
            {"id": event.cliente.id, "name": event.cliente.name}
            if event.cliente
            else None
        ),
        "lavoro": (
            {"id": event.lavoro.id, "descrizione": event.lavoro.descrizione}
            if event.lavoro
            else None
        ),
    }


def serialize_dashboard_quote(preventivo):
    return {
        "id": preventivo.id,
        "url": url_for("preventivi.visualizza_preventivo", id=preventivo.id),
        "descrizione": preventivo.descrizione,
        "stato": preventivo.stato,
        "data_creazione": (
            preventivo.data_creazione.isoformat()
            if preventivo.data_creazione
            else None
        ),
        "totale_preventivo": float(preventivo.totale_preventivo) if preventivo.totale_preventivo is not None else None,
        "cliente": (
            {"id": preventivo.cliente.id, "name": preventivo.cliente.name}
            if preventivo.cliente
            else None
        ),
    }


def apply_task_payload(task, data, partial=False):
    if not partial or "name" in data:
        task.name = (data.get("name") or "").strip()
    if not partial or "note" in data:
        task.note = (data.get("note") or "").strip() or None
    if not partial or "category" in data:
        task.category = data.get("category") or "generale"
    if not partial or "status" in data:
        task.status = data.get("status") or "da_fare"
    if not partial or "priority" in data:
        task.priority = data.get("priority") or "media"
    if not partial or "due_date" in data:
        task.due_date = parse_optional_date(data.get("due_date"))
    if not partial or "lavoro_id" in data:
        task.lavoro_id = parse_optional_id(data.get("lavoro_id"))
    if not partial or "cliente_id" in data:
        task.cliente_id = parse_optional_id(data.get("cliente_id"))

    if not task.name:
        raise ValueError("Il titolo task e obbligatorio.")
    if task.category not in TASK_CATEGORIES:
        raise ValueError("Categoria task non valida.")
    if task.status not in TASK_STATUSES:
        raise ValueError("Stato task non valido.")
    if task.priority not in TASK_PRIORITIES:
        raise ValueError("Priorita task non valida.")


@bp.get("/api/clienti/getall")
@login_required
def get_clienti():
    clienti = Cliente.query.all()
    return api_response(
        data=[
            {
                "id": c.id,
                "nome": c.name,
                "telefono": c.telefono,
                "email": c.email,
                "note": c.note,
                "colore": c.colore,
                "count_lavori": Lavoro.query.filter_by(cliente_id=c.id).count(),
            }
            for c in clienti
        ]
    )


def get_notifications():
    today = date.today()
    three_days = today + timedelta(days=3)
    closed_statuses = ("completata", "annullata")
    notifs = []

    overdue = (
        Task.query.filter(Task.due_date < today)
        .filter(~Task.status.in_(closed_statuses))
        .order_by(Task.due_date.asc())
        .limit(10)
        .all()
    )
    for t in overdue:
        notifs.append(
            {
                "type": "overdue_task",
                "icon": "bi-exclamation-triangle",
                "title": f"Task scaduta: {t.name}",
                "description": f"Scaduta il {t.due_date.strftime('%d/%m/%Y')}",
                "url": url_for("tasks.task_edit", task_id=t.id),
            }
        )

    due_soon = (
        Task.query.filter(Task.due_date >= today)
        .filter(Task.due_date <= three_days)
        .filter(~Task.status.in_(closed_statuses))
        .order_by(Task.due_date.asc())
        .limit(10)
        .all()
    )
    for t in due_soon:
        notifs.append(
            {
                "type": "task_due_soon",
                "icon": "bi-alarm",
                "title": f"Task in scadenza: {t.name}",
                "description": f"Scade il {t.due_date.strftime('%d/%m/%Y')}",
                "url": url_for("tasks.task_edit", task_id=t.id),
            }
        )

    upcoming_pub = (
        EditorialPublication.query.filter(
            EditorialPublication.publication_date >= today,
            EditorialPublication.publication_date <= three_days,
            EditorialPublication.status.in_(["programmato", "approvato"]),
        )
        .order_by(EditorialPublication.publication_date.asc())
        .limit(10)
        .all()
    )
    for p in upcoming_pub:
        cliente_name = p.cliente.name if p.cliente else ""
        notifs.append(
            {
                "type": "upcoming_publication",
                "icon": "bi-calendar2-week",
                "title": f"Pubblicazione: {p.title}",
                "description": f"{cliente_name} - {p.publication_date.strftime('%d/%m/%Y')}",
                "url": url_for(
                    "editorial_calendar.editorial_edit", publication_id=p.id
                ),
            }
        )

    draft_statuses = ("bozza", "draft")
    pending_quotes = (
        Preventivo.query.filter(
            db.func.lower(Preventivo.stato).in_(draft_statuses)
        )
        .order_by(Preventivo.data_creazione.desc())
        .limit(10)
        .all()
    )
    for q in pending_quotes:
        notifs.append(
            {
                "type": "pending_quote",
                "icon": "bi-file-earmark-text",
                "title": f"Preventivo da completare: {q.descrizione}",
                "description": q.cliente.name if q.cliente else "",
                "url": url_for("preventivi.visualizza_preventivo", id=q.id),
            }
        )

    pending_finance = (
        FinancialMovement.query.filter_by(movement_status="prevista")
        .order_by(FinancialMovement.movement_date.asc())
        .limit(10)
        .all()
    )
    for m in pending_finance:
        segno = "entrata" if m.movement_type == "entrata" else "uscita"
        notifs.append(
            {
                "type": "pending_finance",
                "icon": "bi-cash-coin",
                "title": f"{m.title} ({segno})",
                "description": f"Previsto il {m.movement_date.strftime('%d/%m/%Y')} - \u20ac{float(m.amount):.2f}",
                "url": url_for("finance.finance_index"),
            }
        )

    return notifs[:30]


def serialize_dashboard_publication(p):
    return {
        "id": p.id,
        "url": url_for("editorial_calendar.editorial_edit", publication_id=p.id),
        "title": p.title,
        "date": p.publication_date.isoformat() if p.publication_date else None,
        "status": p.status,
        "client_approval_status": p.client_approval_status,
        "cliente": {"id": p.cliente.id, "name": p.cliente.name} if p.cliente else None,
        "platforms": p.get_platforms(),
    }


def build_today_items(today_tasks, today_events, today_followups, pending_approvals, overdue_count):
    items = []

    for task in today_tasks:
        items.append({
            "type": "task_in_scadenza",
            "label": f"Task in scadenza: {task.name}",
            "priority": task.priority,
            "due_date": task.due_date.isoformat() if task.due_date else None,
            "url": url_for("tasks.task_edit", task_id=task.id),
        })

    for event in today_events:
        items.append({
            "type": "evento",
            "label": f"Evento: {event.title}",
            "time": event.start_datetime.strftime("%H:%M") if event.start_datetime else None,
            "url": url_for("calendar.calendar_edit", event_id=event.id),
        })

    for p in pending_approvals[:3]:
        items.append({
            "type": "da_approvare",
            "label": f"Approvazione: {p.title}",
            "cliente": p.cliente.name if p.cliente else None,
            "url": url_for("editorial_calendar.editorial_edit", publication_id=p.id),
        })

    for p in today_followups[:2]:
        items.append({
            "type": "followup",
            "label": f"Follow-up preventivo: {p.descrizione}",
            "url": url_for("preventivi.visualizza_preventivo", id=p.id),
        })

    return items[:8]


def build_recent_updates(tasks, quotes, jobs):
    updates = []
    for t in tasks:
        updates.append({
            "type": "task",
            "label": f"Task: {t.name}",
            "status": t.status,
            "url": url_for("tasks.task_edit", task_id=t.id),
            "ts": (t.updated_at or t.created_at).isoformat() if (t.updated_at or t.created_at) else None,
        })
    for q in quotes:
        updates.append({
            "type": "preventivo",
            "label": f"Preventivo: {q.descrizione}",
            "status": q.stato,
            "url": url_for("preventivi.visualizza_preventivo", id=q.id),
            "ts": q.data_creazione.isoformat() if q.data_creazione else None,
        })
    for j in jobs:
        updates.append({
            "type": "lavoro",
            "label": f"Lavoro: {j.descrizione}",
            "status": j.stato,
            "url": url_for("lavori.lavoro_page", lavoro_id=j.id),
            "ts": None,
        })
    updates.sort(key=lambda x: x["ts"] or "", reverse=True)
    return updates[:5]


@bp.get("/api/dashboard/summary")
@login_required
def get_dashboard_summary():
    try:
        today = date.today()
        due_soon_limit = today + timedelta(days=7)
        now = datetime.combine(today, time.min)
        upcoming_limit = now + timedelta(days=7)
        closed_task_statuses = ("completata", "annullata")
        closed_job_statuses = ("completato", "completata", "chiuso", "chiusa")
        draft_quote_statuses = ("bozza", "draft")
        accepted_quote_statuses = ("accettato", "accettata", "approvato", "approvata")
        finance_data = finance_summary(today.year, today.month)

        open_tasks = Task.query.filter(~Task.status.in_(closed_task_statuses))
        task_open_count = open_tasks.count()
        task_due_soon_count = (
            open_tasks.filter(Task.due_date >= today)
            .filter(Task.due_date <= due_soon_limit)
            .count()
        )
        overdue_task_count = open_tasks.filter(Task.due_date < today).count()

        upcoming_events = (
            CalendarEvent.query.filter(CalendarEvent.start_datetime >= now)
            .filter(CalendarEvent.start_datetime <= upcoming_limit)
            .order_by(CalendarEvent.start_datetime.asc())
            .limit(5)
            .all()
        )

        recent_tasks = (
            Task.query.order_by(Task.updated_at.desc(), Task.created_at.desc()).limit(5).all()
        )
        recent_quotes = (
            Preventivo.query.order_by(Preventivo.data_creazione.desc()).limit(5).all()
        )
        unread_mail_count = EmailMessage.query.filter(
            EmailMessage.direction == "inbound",
            EmailMessage.is_read.is_(False),
        ).count()

        notifications = get_notifications()

        tomorrow = today + timedelta(days=1)
        upcoming_publications = (
            EditorialPublication.query
            .filter(EditorialPublication.publication_date >= today)
            .filter(EditorialPublication.publication_date <= upcoming_limit)
            .order_by(EditorialPublication.publication_date.asc())
            .limit(8)
            .all()
        )

        pending_approval_publications = (
            EditorialPublication.query
            .filter(EditorialPublication.client_approval_status == "da_approvare")
            .filter(EditorialPublication.status != "annullato")
            .order_by(EditorialPublication.publication_date.asc())
            .limit(5)
            .all()
        )

        pending_quotes = (
            Preventivo.query
            .filter(db.func.lower(Preventivo.stato).in_(("inviato", "inviata", "in_attesa")))
            .order_by(Preventivo.data_creazione.desc())
            .all()
        )

        expected_income_count = FinancialMovement.query.filter(
            FinancialMovement.movement_type == "entrata",
            FinancialMovement.movement_status == "prevista",
        ).count()
        expected_income_sum = (
            db.session.query(db.func.coalesce(db.func.sum(FinancialMovement.amount), 0))
            .filter(
                FinancialMovement.movement_type == "entrata",
                FinancialMovement.movement_status == "prevista",
            )
            .scalar()
        )

        today_events = (
            CalendarEvent.query.filter(CalendarEvent.start_datetime >= now)
            .filter(CalendarEvent.start_datetime < now + timedelta(days=1))
            .order_by(CalendarEvent.start_datetime.asc())
            .limit(3)
            .all()
        )

        today_tasks = (
            open_tasks.filter(Task.due_date == today)
            .order_by(Task.priority.asc(), Task.due_date.asc())
            .limit(3)
            .all()
        )

        today_followups = (
            Preventivo.query
            .filter(Preventivo.data_followup == today)
            .order_by(Preventivo.data_creazione.desc())
            .all()
        )

        recent_jobs = (
            Lavoro.query.order_by(Lavoro.id.desc()).limit(3).all()
        )

        data = {
            "notifications": notifications,
            "open_task_count": task_open_count,
            "task_due_soon_count": task_due_soon_count,
            "overdue_task_count": overdue_task_count,
            "upcoming_events_count": (
                CalendarEvent.query.filter(CalendarEvent.start_datetime >= now)
                .filter(CalendarEvent.start_datetime <= upcoming_limit)
                .count()
            ),
            "active_clients_count": Cliente.query.count(),
            "active_jobs_count": Lavoro.query.filter(
                db.or_(
                    Lavoro.stato.is_(None),
                    ~db.func.lower(Lavoro.stato).in_(closed_job_statuses),
                )
            ).count(),
            "pending_quotes_count": len(pending_quotes),
            "draft_quotes_count": Preventivo.query.filter(
                db.func.lower(Preventivo.stato).in_(draft_quote_statuses)
            ).count(),
            "accepted_quotes_count": Preventivo.query.filter(
                db.func.lower(Preventivo.stato).in_(accepted_quote_statuses)
            ).count(),
            "upcoming_publications_count": len(upcoming_publications),
            "expected_income_count": expected_income_count,
            "expected_income_sum": float(expected_income_sum),
            "recent_tasks": [serialize_dashboard_task(task) for task in recent_tasks],
            "upcoming_events": [
                serialize_dashboard_event(event) for event in upcoming_events
            ],
            "upcoming_publications": [
                serialize_dashboard_publication(p) for p in upcoming_publications
            ],
            "recent_quotes": [
                serialize_dashboard_quote(preventivo) for preventivo in recent_quotes
            ],
            "today_items": build_today_items(today_tasks, today_events, today_followups, pending_approval_publications, overdue_task_count),
            "recent_updates": build_recent_updates(recent_tasks[:2], recent_quotes[:2], recent_jobs[:2]),
            "unread_mail_count": unread_mail_count,
            "current_balance": finance_data["current_balance"],
            "month_income_effective": finance_data["month_income_effective"],
            "month_income_expected": finance_data["month_income_expected"],
            "month_expenses_fixed": finance_data["month_expenses_fixed"],
            "month_expenses_variable": finance_data["month_expenses_variable"],
            "month_expenses_total": finance_data["month_expenses_total"],
            "month_balance": finance_data["month_balance"],
        }
        return api_response(data=data)
    except Exception as e:
        return api_response(False, None, str(e), 500)


@bp.get("/api/finance")
@login_required
def get_finance_movements():
    movements = FinancialMovement.query.order_by(
        FinancialMovement.movement_date.desc(), FinancialMovement.id.desc()
    ).all()
    return api_response(data=[movement.to_dict() for movement in movements])


@bp.get("/api/finance/<int:movement_id>")
@login_required
def get_finance_movement(movement_id):
    movement = db.session.get(FinancialMovement, movement_id)
    if movement is None:
        return api_response(False, None, "Movimento non trovato.", 404)
    return api_response(data=movement.to_dict())


@bp.post("/api/finance")
@role_required("admin", "operatore")
def create_finance_movement():
    data = request.get_json(silent=True) or {}
    movement = FinancialMovement()

    try:
        apply_financial_payload(movement, data, created_by=g.current_user.id if g.get("current_user") else None)
        db.session.add(movement)
        db.session.commit()
    except ValueError as exc:
        db.session.rollback()
        return api_response(False, None, str(exc), 400)

    return api_response(data=movement.to_dict(), status=201)


@bp.patch("/api/finance/<int:movement_id>")
@role_required("admin", "operatore")
def update_finance_movement(movement_id):
    movement = db.session.get(FinancialMovement, movement_id)
    if movement is None:
        return api_response(False, None, "Movimento non trovato.", 404)
    data = request.get_json(silent=True) or {}

    try:
        apply_financial_payload(movement, data, partial=True)
        db.session.commit()
    except ValueError as exc:
        db.session.rollback()
        return api_response(False, None, str(exc), 400)

    return api_response(data=movement.to_dict())


@bp.delete("/api/finance/<int:movement_id>")
@role_required("admin", "operatore")
def delete_finance_movement(movement_id):
    movement = db.session.get(FinancialMovement, movement_id)
    if movement is None:
        return api_response(False, None, "Movimento non trovato.", 404)
    deleted = movement.to_dict()
    delete_financial_movement(movement)
    db.session.commit()
    return api_response(data=deleted)


@bp.get("/api/emails")
@login_required
def get_email_logs():
    query = EmailLog.query
    cliente_id = request.args.get("cliente_id", type=int)
    if cliente_id:
        query = query.filter_by(cliente_id=cliente_id)
    email_logs = query.order_by(EmailLog.sent_at.desc(), EmailLog.id.desc()).all()
    return api_response(data=[email_log.to_dict() for email_log in email_logs])


@bp.get("/api/emails/<int:email_id>")
@login_required
def get_email_log(email_id):
    email_log = db.session.get(EmailLog, email_id)
    if email_log is None:
        return api_response(False, None, "Comunicazione non trovata.", 404)
    return api_response(data=email_log.to_dict())


@bp.post("/api/emails")
@role_required("admin", "operatore")
def create_email_log():
    data = request.get_json(silent=True) or {}
    email_log = EmailLog()

    try:
        email_log.created_by = g.current_user.id if g.get("current_user") else None
        apply_email_payload(email_log, data)
        db.session.add(email_log)
        db.session.commit()
    except ValueError as exc:
        db.session.rollback()
        return api_response(False, None, str(exc), 400)

    return api_response(data=email_log.to_dict(), status=201)


@bp.patch("/api/emails/<int:email_id>")
@role_required("admin", "operatore")
def update_email_log(email_id):
    email_log = db.session.get(EmailLog, email_id)
    if email_log is None:
        return api_response(False, None, "Comunicazione non trovata.", 404)
    data = request.get_json(silent=True) or {}

    try:
        apply_email_payload(email_log, data, partial=True)
        db.session.commit()
    except ValueError as exc:
        db.session.rollback()
        return api_response(False, None, str(exc), 400)

    return api_response(data=email_log.to_dict())


@bp.delete("/api/emails/<int:email_id>")
@role_required("admin", "operatore")
def delete_email_log(email_id):
    email_log = db.session.get(EmailLog, email_id)
    if email_log is None:
        return api_response(False, None, "Comunicazione non trovata.", 404)
    deleted = email_log.to_dict()
    db.session.delete(email_log)
    db.session.commit()
    return api_response(data=deleted)


@bp.get("/api/finance/summary")
@login_required
def get_finance_summary():
    today = date.today()
    year = request.args.get("year", today.year, type=int)
    month = request.args.get("month", today.month, type=int)
    if month < 1 or month > 12:
        return api_response(False, None, "Mese non valido.", 400)
    return api_response(data=finance_summary(year, month))


@bp.get("/api/tasks")
@login_required
def get_tasks():
    tasks = Task.query.order_by(Task.created_at.desc()).all()
    return api_response(data=[task.to_dict() for task in tasks])


@bp.get("/api/tasks/<int:task_id>")
@login_required
def get_task(task_id):
    task = db.session.get(Task, task_id)
    if task is None:
        return api_response(False, None, "Task non trovata.", 404)
    return api_response(data=task.to_dict())


@bp.post("/api/tasks")
@role_required("admin", "operatore")
def create_task():
    data = request.get_json(silent=True) or {}
    task = Task()

    try:
        apply_task_payload(task, data)
        db.session.add(task)
        db.session.commit()
    except ValueError as exc:
        db.session.rollback()
        return api_response(False, None, str(exc), 400)

    return api_response(data=task.to_dict(), status=201)


@bp.patch("/api/tasks/<int:task_id>")
@role_required("admin", "operatore")
def update_task(task_id):
    task = db.session.get(Task, task_id)
    if task is None:
        return api_response(False, None, "Task non trovata.", 404)
    data = request.get_json(silent=True) or {}

    try:
        apply_task_payload(task, data, partial=True)
        db.session.commit()
    except ValueError as exc:
        db.session.rollback()
        return api_response(False, None, str(exc), 400)

    return api_response(data=task.to_dict())


@bp.delete("/api/tasks/<int:task_id>")
@role_required("admin", "operatore")
def delete_task(task_id):
    task = db.session.get(Task, task_id)
    if task is None:
        return api_response(False, None, "Task non trovata.", 404)
    task.status = "annullata"
    db.session.commit()
    return api_response(data=task.to_dict())


@bp.get("/api/calendar/events")
@login_required
def get_calendar_events():
    events = [event.to_dict() for event in CalendarEvent.query.all()]
    task_events = [
        task_due_date_to_calendar_event(task)
        for task in Task.query.filter(Task.due_date.isnot(None)).all()
    ]
    all_events = events + task_events
    all_events.sort(key=lambda event: event["start_datetime"] or "")
    return api_response(data=all_events)


@bp.get("/api/calendar/events/<int:event_id>")
@login_required
def get_calendar_event(event_id):
    event = db.session.get(CalendarEvent, event_id)
    if event is None:
        return api_response(False, None, "Evento non trovato.", 404)
    return api_response(data=event.to_dict())


@bp.post("/api/calendar/events")
@role_required("admin", "operatore")
def create_calendar_event():
    data = request.get_json(silent=True) or {}
    event = CalendarEvent()

    try:
        apply_calendar_payload(event, data)
        db.session.add(event)
        db.session.commit()
    except ValueError as exc:
        db.session.rollback()
        return api_response(False, None, str(exc), 400)

    return api_response(data=event.to_dict(), status=201)


@bp.patch("/api/calendar/events/<int:event_id>")
@role_required("admin", "operatore")
def update_calendar_event(event_id):
    event = db.session.get(CalendarEvent, event_id)
    if event is None:
        return api_response(False, None, "Evento non trovato.", 404)
    data = request.get_json(silent=True) or {}

    try:
        apply_calendar_payload(event, data, partial=True)
        db.session.commit()
    except ValueError as exc:
        db.session.rollback()
        return api_response(False, None, str(exc), 400)

    return api_response(data=event.to_dict())


@bp.delete("/api/calendar/events/<int:event_id>")
@role_required("admin", "operatore")
def delete_calendar_event(event_id):
    event = db.session.get(CalendarEvent, event_id)
    if event is None:
        return api_response(False, None, "Evento non trovato.", 404)
    deleted = event.to_dict()
    db.session.delete(event)
    db.session.commit()
    return api_response(data=deleted)


@bp.get("/api/lavori/getall")
@login_required
def get_lavori():
    lavori = Lavoro.query.all()
    return api_response(
        data=[
            {
                "id": l.id,
                "descrizione": l.descrizione,
                "data_inizio": l.data_inizio,
                "data_fine": l.data_fine,
                "data_pagamento": l.data_pagamento,
                "stato": l.stato,
                "priorita": l.priorita,
                "preventivato": l.preventivato,
                "cliente": {
                    "id": l.cliente.id,
                    "colore": l.cliente.colore,
                    "name": l.cliente.name,
                },
                "note": l.note,
                "preventivo_pdf_path": l.preventivo_pdf_path,
            }
            for l in lavori
        ]
    )


@bp.get("/api/lavori/get/<int:id>")
@login_required
def get_lavoro_byID(id):
    lavoro = db.session.get(Lavoro, id)
    if lavoro is None:
        return api_response(False, None, "Lavoro non trovato.", 404)
    return api_response(
        data={
            "id": lavoro.id,
            "descrizione": lavoro.descrizione,
            "data_inizio": lavoro.data_inizio,
            "data_fine": lavoro.data_fine,
            "data_pagamento": lavoro.data_pagamento,
            "priorita": lavoro.priorita,
            "stato": lavoro.stato,
            "preventivato": lavoro.preventivato,
            "note": lavoro.note,
            "cliente": {
                "nome": lavoro.cliente.name,
                "id": lavoro.cliente.id,
                "colore": lavoro.cliente.colore,
            },
        }
    )


@bp.get("/api/clienti/get/<int:cliente_id>")
@login_required
def get_cliente_byID(cliente_id):
    c = db.session.get(Cliente, cliente_id)
    if c is None:
        return api_response(False, None, "Cliente non trovato.", 404)
    lavori = Lavoro.query.filter_by(cliente_id=cliente_id)
    countLavori = lavori.count()

    return api_response(
        data={
            "id": c.id,
            "nome": c.name,
            "ragsoc": c.ragsoc,
            "indirizzo": c.indirizzo,
            "citta": c.citta,
            "cap": c.cap,
            "provincia": c.provincia,
            "email": c.email,
            "telefono": c.telefono,
            "p_iva": c.p_iva,
            "sdi": c.sdi,
            "pec": c.pec,
            "colore": c.colore,
            "note": c.note,
            "count_lavori": countLavori,
            "lavori": [
                {
                    "id": lavoro.id,
                    "descrizione": lavoro.descrizione,
                    "stato": lavoro.stato,
                    "preventivato": lavoro.preventivato,
                    "data_inizio": lavoro.data_inizio,
                    "data_fine": lavoro.data_fine,
                    "data_pagamento": lavoro.data_pagamento,
                    "priorita": lavoro.priorita,
                    "note": lavoro.note,
                }
                for lavoro in lavori
            ],
        }
    )


@bp.get("/api/clienti/getid/<string:nome>")
@login_required
def get_ID_by_name(nome):
    cliente = Cliente.query.filter_by(name=nome).first()
    if cliente is None:
        return api_response(False, None, "Cliente non trovato.", 404)
    return api_response(data={"id": cliente.id})


@bp.get("/api/preventivi/getall")
@login_required
def get_preventivi():
    preventivi = Preventivo.query.all()
    from flask import url_for
    lavori_con_pdf = Lavoro.query.filter(
        Lavoro.preventivo_pdf_path.isnot(None),
        Lavoro.preventivo_pdf_path != "",
    ).all()

    result = [
        {
            "id": p.id,
            "descrizione": p.descrizione,
            "data": p.data_creazione,
            "cliente": p.cliente.name if p.cliente else None,
            "stato": p.stato,
            "totale_preventivo": p.totale_preventivo,
            "data_creazione": p.data_creazione.isoformat() if p.data_creazione else None,
            "lavoro": {"id": p.lavoro.id, "descrizione": p.lavoro.descrizione} if p.lavoro else None,
            "source": "erp",
            "pdf_url": None,
            "righe": [
                {
                    "id": riga.id,
                    "qty": riga.qty,
                    "descrizione": riga.descrizione,
                    "prezzo_ie": riga.prezzo_ie,
                    "prezzo_ii": riga.prezzo_ii,
                    "totale_riga": riga.totale_riga,
                }
                for riga in p.righe
            ],
        }
        for p in preventivi
    ]

    for lavoro in lavori_con_pdf:
        cliente_name = lavoro.cliente.name if lavoro.cliente else "-"
        data_pdf = None
        if lavoro.data_inizio:
            data_pdf = lavoro.data_inizio.isoformat()
        elif lavoro.data_fine:
            data_pdf = lavoro.data_fine.isoformat()
        result.append({
            "id": f"ext_{lavoro.id}",
            "descrizione": lavoro.descrizione,
            "data": data_pdf,
            "cliente": cliente_name,
            "stato": "pdf_esterno",
            "totale_preventivo": lavoro.preventivato,
            "data_creazione": data_pdf,
            "lavoro": {"id": lavoro.id, "descrizione": lavoro.descrizione},
            "source": "pdf_esterno",
            "pdf_url": url_for("static", filename=lavoro.preventivo_pdf_path),
            "righe": [],
        })

    return api_response(data=result)


@bp.get("/api/preventivi/get/<int:id>")
@login_required
def get_preventivo_byID(id):
    preventivo = Preventivo.query.filter_by(id=id).first()
    if preventivo is None:
        return api_response(False, None, "Preventivo non trovato.", 404)
    return api_response(
        data={
            "id": preventivo.id,
            "data": preventivo.data_creazione,
            "stato": preventivo.stato,
            "lavoro": {"id": preventivo.lavoro.id, "descrizione": preventivo.lavoro.descrizione} if preventivo.lavoro else None,
            "totale_preventivo": float(preventivo.totale_preventivo) if preventivo.totale_preventivo is not None else None,
            "cliente": {
                "nome": preventivo.cliente.name,
                "ragsoc": preventivo.cliente.ragsoc,
                "indirizzo": preventivo.cliente.indirizzo,
                "citta": preventivo.cliente.citta,
                "cap": preventivo.cliente.cap,
                "provincia": preventivo.cliente.provincia,
                "email": preventivo.cliente.email,
                "telefono": preventivo.cliente.telefono,
                "p_iva": preventivo.cliente.p_iva,
                "sdi": preventivo.cliente.sdi,
                "pec": preventivo.cliente.pec,
                "colore": preventivo.cliente.colore,
            },
            "righe": [
                {
                    "id": riga.id,
                    "qty": riga.qty,
                    "descrizione": riga.descrizione,
                    "prezzo_ie": float(riga.prezzo_ie),
                    "prezzo_ii": float(riga.prezzo_ii),
                    "totale_riga": float(riga.totale_riga),
                }
                for riga in preventivo.righe
            ],
        }
    )
