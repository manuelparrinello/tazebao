from datetime import date, datetime, time, timedelta

from flask import Blueprint, g, jsonify, request, url_for

from ..auth import login_required
from ..extensions import db
from ..finance_service import (
    apply_financial_payload,
    delete_financial_movement,
    finance_summary,
)
from ..models import CalendarEvent, Cliente, EmailLog, FinancialMovement, Lavoro, Preventivo
from ..models import (
    CALENDAR_EVENT_TYPES,
    EMAIL_DIRECTIONS,
    TASK_CATEGORIES,
    TASK_PRIORITIES,
    TASK_STATUSES,
    Task,
)


bp = Blueprint("api", __name__)


def api_response(success=True, data=None, error=None, status=200):
    return jsonify({"success": success, "data": data, "error": error}), status


def parse_optional_date(value):
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%d").date()


def parse_optional_datetime(value):
    if not value:
        return None
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return datetime.fromisoformat(value)


def parse_optional_id(value):
    if value in (None, ""):
        return None
    return int(value)


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
    if not partial or "assigned_user_id" in data:
        event.assigned_user_id = parse_optional_id(data.get("assigned_user_id"))

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
        "assigned_user_id": task.assignee_id,
        "assigned_user": (
            {
                "id": task.assignee.id,
                "name": task.assignee.name,
                "email": task.assignee.email,
            }
            if task.assignee
            else None
        ),
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
        "url": url_for("visualizza_preventivo", id=preventivo.id),
        "descrizione": preventivo.descrizione,
        "stato": preventivo.stato,
        "data_creazione": (
            preventivo.data_creazione.isoformat()
            if preventivo.data_creazione
            else None
        ),
        "totale_preventivo": preventivo.totale_preventivo,
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
    if not partial or "assignee_id" in data:
        task.assignee_id = parse_optional_id(data.get("assignee_id"))

    if not task.name:
        raise ValueError("Il titolo task e obbligatorio.")
    if task.category not in TASK_CATEGORIES:
        raise ValueError("Categoria task non valida.")
    if task.status not in TASK_STATUSES:
        raise ValueError("Stato task non valido.")
    if task.priority not in TASK_PRIORITIES:
        raise ValueError("Priorita task non valida.")


@bp.get("/api/clienti/getall")
def get_clienti():
    clienti = Cliente.query.all()
    return jsonify(
        [
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


@bp.get("/api/dashboard/summary")
@login_required
def get_dashboard_summary():
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

    data = {
        "task_open_count": task_open_count,
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
        "draft_quotes_count": Preventivo.query.filter(
            db.func.lower(Preventivo.stato).in_(draft_quote_statuses)
        ).count(),
        "accepted_quotes_count": Preventivo.query.filter(
            db.func.lower(Preventivo.stato).in_(accepted_quote_statuses)
        ).count(),
        "recent_tasks": [serialize_dashboard_task(task) for task in recent_tasks],
        "upcoming_events": [
            serialize_dashboard_event(event) for event in upcoming_events
        ],
        "recent_quotes": [
            serialize_dashboard_quote(preventivo) for preventivo in recent_quotes
        ],
        "current_balance": finance_data["current_balance"],
        "month_income_effective": finance_data["month_income_effective"],
        "month_income_expected": finance_data["month_income_expected"],
        "month_expenses_fixed": finance_data["month_expenses_fixed"],
        "month_expenses_variable": finance_data["month_expenses_variable"],
        "month_expenses_total": finance_data["month_expenses_total"],
        "month_balance": finance_data["month_balance"],
    }
    return api_response(data=data)


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
@login_required
def create_finance_movement():
    data = request.get_json(silent=True) or {}
    movement = FinancialMovement()

    try:
        apply_financial_payload(movement, data)
        db.session.add(movement)
        db.session.commit()
    except ValueError as exc:
        db.session.rollback()
        return api_response(False, None, str(exc), 400)

    return api_response(data=movement.to_dict(), status=201)


@bp.patch("/api/finance/<int:movement_id>")
@login_required
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
@login_required
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
@login_required
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
@login_required
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
@login_required
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
@login_required
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
@login_required
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
@login_required
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
@login_required
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
@login_required
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
@login_required
def delete_calendar_event(event_id):
    event = db.session.get(CalendarEvent, event_id)
    if event is None:
        return api_response(False, None, "Evento non trovato.", 404)
    deleted = event.to_dict()
    db.session.delete(event)
    db.session.commit()
    return api_response(data=deleted)


@bp.get("/api/lavori/getall")
def get_lavori():
    lavori = Lavoro.query.all()
    return jsonify(
        [
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
            }
            for l in lavori
        ]
    )


@bp.get("/api/lavori/get/<int:id>")
def get_lavoro_byID(id):
    lavoro = Lavoro.query.get_or_404(id)
    return jsonify(
        {
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
def get_cliente_byID(cliente_id):
    c = Cliente.query.get_or_404(cliente_id)
    lavori = Lavoro.query.filter_by(cliente_id=cliente_id)
    countLavori = lavori.count()

    return jsonify(
        {
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
def get_ID_by_name(nome):
    cliente = Cliente.query.filter_by(name=nome).first()
    id = cliente.id
    print(id)
    return jsonify({"id": id})


@bp.get("/api/preventivi/getall")
def get_preventivi():
    preventivi = Preventivo.query.all()
    return jsonify(
        [
            {
                "id": p.id,
                "descrizione": p.descrizione,
                "data": p.data_creazione,
                "cliente": Cliente.query.filter_by(id=p.cliente_id).first_or_404().name,
                "stato": p.stato,
                "totale_preventivo": p.totale_preventivo,
                "data_creazione": p.data_creazione.isoformat(),
                "lavoro": p.lavoro,
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
    )


@bp.get("/api/preventivi/get/<int:id>")
def get_preventivo_byID(id):
    preventivo = Preventivo.query.filter_by(id=id).first_or_404()
    return jsonify(
        {
            "id": preventivo.id,
            "cliente": preventivo.cliente,
            "data": preventivo.data_creazione,
            "stato": preventivo.stato,
            "lavoro": preventivo.lavoro,
            "totale_preventivo": float(preventivo.totale_preventivo),
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
