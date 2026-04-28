from datetime import datetime, time

from flask import Blueprint, jsonify, request

from ..auth import login_required
from ..extensions import db
from ..models import CalendarEvent, Cliente, Lavoro, Preventivo
from ..models import CALENDAR_EVENT_TYPES, TASK_CATEGORIES, TASK_PRIORITIES, TASK_STATUSES, Task


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
