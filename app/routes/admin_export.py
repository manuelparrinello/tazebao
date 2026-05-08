import csv
import io
import json
from datetime import date, datetime
from decimal import Decimal

from flask import Blueprint, Response, abort, render_template

from ..auth import role_required
from ..models import (
    CalendarEvent,
    Cliente,
    EditorialPublication,
    FinancialMovement,
    Lavoro,
    Preventivo,
    Task,
    User,
)


bp = Blueprint("admin_export", __name__)


def export_value(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if value is None:
        return ""
    return value


def normalize_row(row):
    return {key: export_value(value) for key, value in row.items()}


def cliente_row(cliente):
    return normalize_row(
        {
            "id": cliente.id,
            "name": cliente.name,
            "ragsoc": cliente.ragsoc,
            "indirizzo": cliente.indirizzo,
            "citta": cliente.citta,
            "cap": cliente.cap,
            "provincia": cliente.provincia,
            "email": cliente.email,
            "telefono": cliente.telefono,
            "p_iva": cliente.p_iva,
            "sdi": cliente.sdi,
            "pec": cliente.pec,
            "colore": cliente.colore,
            "note": cliente.note,
        }
    )


def lavoro_row(lavoro):
    return normalize_row(
        {
            "id": lavoro.id,
            "descrizione": lavoro.descrizione,
            "data_inizio": lavoro.data_inizio,
            "data_fine": lavoro.data_fine,
            "data_pagamento": lavoro.data_pagamento,
            "stato": lavoro.stato,
            "priorita": lavoro.priorita,
            "note": lavoro.note,
            "preventivato": lavoro.preventivato,
            "cliente_id": lavoro.cliente_id,
        }
    )


def task_row(task):
    return normalize_row(
        {
            "id": task.id,
            "name": task.name,
            "note": task.note,
            "category": task.category,
            "status": task.status,
            "priority": task.priority,
            "due_date": task.due_date,
            "lavoro_id": task.lavoro_id,
            "cliente_id": task.cliente_id,
            "assignee_id": task.assignee_id,
            "created_at": task.created_at,
            "updated_at": task.updated_at,
        }
    )


def preventivo_row(preventivo):
    return normalize_row(
        {
            "id": preventivo.id,
            "descrizione": preventivo.descrizione,
            "cliente_id": preventivo.cliente_id,
            "data_creazione": preventivo.data_creazione,
            "stato": preventivo.stato,
            "totale_preventivo": preventivo.totale_preventivo,
            "lavoro_id": preventivo.lavoro_id,
        }
    )


def calendar_row(event):
    return normalize_row(
        {
            "id": event.id,
            "title": event.title,
            "description": event.description,
            "event_type": event.event_type,
            "start_datetime": event.start_datetime,
            "end_datetime": event.end_datetime,
            "cliente_id": event.cliente_id,
            "lavoro_id": event.lavoro_id,
            "task_id": event.task_id,
            "assigned_user_id": event.assigned_user_id,
            "created_at": event.created_at,
            "updated_at": event.updated_at,
        }
    )


def finance_row(movement):
    return normalize_row(
        {
            "id": movement.id,
            "title": movement.title,
            "description": movement.description,
            "movement_type": movement.movement_type,
            "movement_status": movement.movement_status,
            "expense_type": movement.expense_type,
            "category": movement.category,
            "amount": movement.amount,
            "movement_date": movement.movement_date,
            "month": movement.month,
            "year": movement.year,
            "cliente_id": movement.cliente_id,
            "lavoro_id": movement.lavoro_id,
            "created_by": movement.created_by,
            "created_at": movement.created_at,
            "updated_at": movement.updated_at,
        }
    )


def editorial_publication_row(publication):
    return normalize_row(
        {
            "id": publication.id,
            "cliente_id": publication.cliente_id,
            "publication_date": publication.publication_date,
            "platform": publication.platform,
            "platforms": ",".join(publication.get_platforms()),
            "content_type": publication.content_type,
            "title": publication.title,
            "caption": publication.caption,
            "preview_image_path": publication.preview_image_path,
            "status": publication.status,
            "client_approval_status": publication.client_approval_status,
            "internal_notes": publication.internal_notes,
            "asset_url": publication.asset_url,
            "created_at": publication.created_at,
            "updated_at": publication.updated_at,
        }
    )


def user_row(user):
    return normalize_row(
        {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "is_active": user.is_active,
            "created_at": user.created_at,
        }
    )


EXPORT_RESOURCES = {
    "clienti": {
        "label": "Clienti",
        "description": "Anagrafiche clienti e dati fiscali principali.",
        "query": lambda: Cliente.query.order_by(Cliente.id.asc()).all(),
        "serializer": cliente_row,
    },
    "lavori": {
        "label": "Lavori",
        "description": "Lavori collegati ai clienti.",
        "query": lambda: Lavoro.query.order_by(Lavoro.id.asc()).all(),
        "serializer": lavoro_row,
    },
    "task": {
        "label": "Task",
        "description": "Task ERP operativi.",
        "query": lambda: Task.query.order_by(Task.id.asc()).all(),
        "serializer": task_row,
    },
    "preventivi": {
        "label": "Preventivi",
        "description": "Testate preventivo, senza righe di dettaglio V1.",
        "query": lambda: Preventivo.query.order_by(Preventivo.id.asc()).all(),
        "serializer": preventivo_row,
    },
    "calendar": {
        "label": "Calendario",
        "description": "Eventi calendario ERP.",
        "query": lambda: CalendarEvent.query.order_by(CalendarEvent.id.asc()).all(),
        "serializer": calendar_row,
    },
    "finance": {
        "label": "Finance",
        "description": "Movimenti economici ERP.",
        "query": lambda: FinancialMovement.query.order_by(FinancialMovement.id.asc()).all(),
        "serializer": finance_row,
    },
    "editorial_publications": {
        "label": "Pubblicazioni editoriali",
        "description": "Piano editoriale social.",
        "query": lambda: EditorialPublication.query.order_by(EditorialPublication.id.asc()).all(),
        "serializer": editorial_publication_row,
    },
    "users": {
        "label": "Utenti",
        "description": "Utenti ERP senza password hash.",
        "query": lambda: User.query.order_by(User.id.asc()).all(),
        "serializer": user_row,
    },
}


def resource_rows(resource):
    config = EXPORT_RESOURCES.get(resource)
    if config is None:
        abort(404)
    return [config["serializer"](item) for item in config["query"]()]


@bp.get("/admin/export")
@role_required("admin")
def export_index():
    return render_template(
        "admin_export.html",
        resources=EXPORT_RESOURCES,
    )


@bp.get("/admin/export/<resource>.csv")
@role_required("admin")
def export_csv(resource):
    rows = resource_rows(resource)
    fieldnames = list(rows[0].keys()) if rows else []
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    if fieldnames:
        writer.writeheader()
        writer.writerows(rows)

    filename = f"{resource}_export.csv"
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@bp.get("/admin/export/<resource>.json")
@role_required("admin")
def export_json(resource):
    rows = resource_rows(resource)
    filename = f"{resource}_export.json"
    payload = json.dumps(rows, ensure_ascii=False, indent=2)
    return Response(
        payload,
        mimetype="application/json; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
