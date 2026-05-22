from flask import Blueprint, current_app, g, jsonify, render_template, request, url_for

from ..auth import login_required
from ..extensions import db
from ..utils.api import api_response


bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    return render_template("app_shell.html")

@bp.route("/app")
@login_required
def app_shell():
    return render_template("app_shell.html")


@bp.route("/test")
def test():
    return render_template("base.html")


@bp.route("/search")
@login_required
def search():
    from ..models import (
        CalendarEvent,
        Cliente,
        EditorialPublication,
        EmailLog,
        EmailMessage,
        FinancialMovement,
        Lavoro,
        Moodboard,
        Preventivo,
        Task,
    )

    term = request.args.get("q", "").strip()

    results = {
        "clienti": [],
        "lavori": [],
        "tasks": [],
        "preventivi": [],
        "finance": [],
        "editoriali": [],
        "calendario": [],
        "email_log": [],
        "email_messages": [],
        "moodboards": [],
    }

    if len(term) >= 2:
        pattern = f"%{term}%"

        results["clienti"] = (
            Cliente.query.filter(
                db.or_(
                    Cliente.name.ilike(pattern),
                    Cliente.ragsoc.ilike(pattern),
                    Cliente.email.ilike(pattern),
                    Cliente.telefono.ilike(pattern),
                    Cliente.p_iva.ilike(pattern),
                    Cliente.citta.ilike(pattern),
                )
            )
            .limit(8)
            .all()
        )

        results["lavori"] = (
            Lavoro.query.filter(Lavoro.descrizione.ilike(pattern)).limit(8).all()
        )

        results["tasks"] = (
            Task.query.filter(
                db.or_(
                    Task.name.ilike(pattern),
                    Task.note.ilike(pattern),
                )
            )
            .limit(8)
            .all()
        )

        results["preventivi"] = (
            Preventivo.query.filter(Preventivo.descrizione.ilike(pattern))
            .limit(8)
            .all()
        )

        results["finance"] = (
            FinancialMovement.query.filter(
                db.or_(
                    FinancialMovement.title.ilike(pattern),
                    FinancialMovement.description.ilike(pattern),
                )
            )
            .limit(8)
            .all()
        )

        results["editoriali"] = (
            EditorialPublication.query.filter(
                db.or_(
                    EditorialPublication.title.ilike(pattern),
                    EditorialPublication.caption.ilike(pattern),
                    EditorialPublication.internal_notes.ilike(pattern),
                )
            )
            .limit(8)
            .all()
        )

        results["calendario"] = (
            CalendarEvent.query.filter(
                db.or_(
                    CalendarEvent.title.ilike(pattern),
                    CalendarEvent.description.ilike(pattern),
                )
            )
            .limit(8)
            .all()
        )

        results["email_log"] = (
            EmailLog.query.filter(
                db.or_(
                    EmailLog.subject.ilike(pattern),
                    EmailLog.email_address.ilike(pattern),
                )
            )
            .limit(8)
            .all()
        )

        results["email_messages"] = (
            EmailMessage.query.filter(
                db.or_(
                    EmailMessage.subject.ilike(pattern),
                    EmailMessage.from_address.ilike(pattern),
                )
            )
            .limit(8)
            .all()
        )

        results["moodboards"] = (
            Moodboard.query.filter(
                db.or_(
                    Moodboard.title.ilike(pattern),
                    Moodboard.description.ilike(pattern),
                )
            )
            .limit(8)
            .all()
        )

    return render_template("search.html", term=term, results=results)


@bp.route("/api/search")
@login_required
def api_search():
    from ..models import (
        Cliente,
        EditorialPublication,
        EmailLog,
        FinancialMovement,
        Lavoro,
        Moodboard,
        Preventivo,
        Task,
        User,
    )

    term = request.args.get("q", "").strip()
    user = g.get("current_user")
    categories = []

    if len(term) >= 2:
        pattern = f"%{term}%"
        MAX_PER = 5
        MAX_TOTAL = 25
        total = 0

        # Clienti
        items = []
        for c in (
            Cliente.query.filter(
                db.or_(
                    Cliente.name.ilike(pattern),
                    Cliente.ragsoc.ilike(pattern),
                    Cliente.email.ilike(pattern),
                    Cliente.telefono.ilike(pattern),
                    Cliente.p_iva.ilike(pattern),
                    Cliente.citta.ilike(pattern),
                )
            )
            .limit(MAX_PER)
            .all()
        ):
            items.append(
                {
                    "type": "cliente",
                    "id": c.id,
                    "label": c.name or c.ragsoc,
                    "subtitle": c.citta or c.email or "",
                    "url": url_for("cliente_page", cliente_id=c.id),
                }
            )
        if items:
            total += len(items)
            categories.append({"key": "clienti", "label": "Clienti", "icon": "bi-people", "results": items})

        if total < MAX_TOTAL:
            items = []
            for l in (
                Lavoro.query.filter(Lavoro.descrizione.ilike(pattern)).limit(MAX_PER).all()
            ):
                items.append(
                    {
                        "type": "lavoro",
                        "id": l.id,
                        "label": l.descrizione,
                        "subtitle": l.cliente.name if l.cliente else "",
                        "url": url_for("lavoro_page", lavoro_id=l.id),
                    }
                )
            if items:
                total += len(items)
                categories.append({"key": "lavori", "label": "Lavori", "icon": "bi-briefcase", "results": items})

        if total < MAX_TOTAL:
            items = []
            for t in (
                Task.query.filter(
                    db.or_(Task.name.ilike(pattern), Task.note.ilike(pattern))
                )
                .limit(MAX_PER)
                .all()
            ):
                items.append(
                    {
                        "type": "task",
                        "id": t.id,
                        "label": t.name,
                        "subtitle": t.cliente.name if t.cliente else "",
                        "url": url_for("tasks.task_edit", task_id=t.id),
                    }
                )
            if items:
                total += len(items)
                categories.append({"key": "tasks", "label": "Task", "icon": "bi-list-check", "results": items})

        if total < MAX_TOTAL:
            items = []
            for p in (
                Preventivo.query.filter(Preventivo.descrizione.ilike(pattern))
                .limit(MAX_PER)
                .all()
            ):
                items.append(
                    {
                        "type": "preventivo",
                        "id": p.id,
                        "label": p.descrizione,
                        "subtitle": p.cliente.name if p.cliente else "",
                        "url": url_for("visualizza_preventivo", id=p.id),
                    }
                )
            if items:
                total += len(items)
                categories.append({"key": "preventivi", "label": "Preventivi", "icon": "bi-receipt", "results": items})

        if total < MAX_TOTAL:
            items = []
            for e in (
                EditorialPublication.query.filter(
                    db.or_(
                        EditorialPublication.title.ilike(pattern),
                        EditorialPublication.caption.ilike(pattern),
                        EditorialPublication.internal_notes.ilike(pattern),
                    )
                )
                .limit(MAX_PER)
                .all()
            ):
                items.append(
                    {
                        "type": "editoriale",
                        "id": e.id,
                        "label": e.title,
                        "subtitle": e.cliente.name if e.cliente else "",
                        "url": url_for(
                            "editorial_calendar.editorial_edit", publication_id=e.id
                        ),
                    }
                )
            if items:
                total += len(items)
                categories.append({"key": "editoriali", "label": "Pubblicazioni", "icon": "bi-calendar2-week", "results": items})

        if total < MAX_TOTAL:
            items = []
            for mb in (
                Moodboard.query.filter(
                    db.or_(
                        Moodboard.title.ilike(pattern),
                        Moodboard.description.ilike(pattern),
                    )
                )
                .limit(MAX_PER)
                .all()
            ):
                items.append(
                    {
                        "type": "moodboard",
                        "id": mb.id,
                        "label": mb.title,
                        "subtitle": mb.cliente.name if mb.cliente else "",
                        "url": url_for("moodboards.moodboard_detail", id=mb.id),
                    }
                )
            if items:
                total += len(items)
                categories.append({"key": "moodboards", "label": "Moodboard", "icon": "bi-images", "results": items})

        if total < MAX_TOTAL:
            items = []
            for log in (
                EmailLog.query.filter(
                    db.or_(
                        EmailLog.subject.ilike(pattern),
                        EmailLog.email_address.ilike(pattern),
                    )
                )
                .limit(MAX_PER)
                .all()
            ):
                items.append(
                    {
                        "type": "email_log",
                        "id": log.id,
                        "label": log.subject or "(nessun oggetto)",
                        "subtitle": log.email_address,
                        "url": url_for("emails.emails_edit", email_id=log.id),
                    }
                )
            if items:
                total += len(items)
                categories.append({"key": "email_log", "label": "Registro email", "icon": "bi-journal-text", "results": items})

        if user and user.is_admin and total < MAX_TOTAL:
            items = []
            for u in (
                User.query.filter(
                    db.or_(
                        User.name.ilike(pattern),
                        User.email.ilike(pattern),
                    )
                )
                .limit(MAX_PER)
                .all()
            ):
                items.append(
                    {
                        "type": "utente",
                        "id": u.id,
                        "label": u.name or u.email,
                        "subtitle": f"{u.role} · {u.email}",
                        "url": url_for("users.users_edit", user_id=u.id),
                    }
                )
            if items:
                total += len(items)
                categories.append({"key": "utenti", "label": "Utenti", "icon": "bi-shield-lock", "results": items})

    return api_response(data={"categories": categories})
