from flask import Blueprint, current_app, jsonify, render_template, request, url_for

from ..auth import login_required
from ..extensions import db


bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    return render_template(
        "index.html",
        title="Home",
        description="Welcome to the Home Page",
        path=current_app.config["DB_PATH"],
    )


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
        CalendarEvent,
        Cliente,
        EditorialPublication,
        FinancialMovement,
        Lavoro,
        Moodboard,
        Preventivo,
        Task,
    )

    term = request.args.get("q", "").strip()
    results = []

    if len(term) >= 2:
        pattern = f"%{term}%"

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
            .limit(3)
            .all()
        ):
            results.append(
                {
                    "type": "cliente",
                    "id": c.id,
                    "label": c.name or c.ragsoc,
                    "subtitle": c.citta or c.email or "",
                    "icon": "bi-people",
                    "url": url_for("cliente_page", cliente_id=c.id),
                }
            )

        for l in (
            Lavoro.query.filter(Lavoro.descrizione.ilike(pattern)).limit(3).all()
        ):
            results.append(
                {
                    "type": "lavoro",
                    "id": l.id,
                    "label": l.descrizione,
                    "subtitle": l.cliente.name if l.cliente else "",
                    "icon": "bi-briefcase",
                    "url": url_for("lavoro_page", lavoro_id=l.id),
                }
            )

        for t in (
            Task.query.filter(
                db.or_(Task.name.ilike(pattern), Task.note.ilike(pattern))
            )
            .limit(3)
            .all()
        ):
            results.append(
                {
                    "type": "task",
                    "id": t.id,
                    "label": t.name,
                    "subtitle": t.cliente.name if t.cliente else "",
                    "icon": "bi-list-check",
                    "url": url_for("tasks.task_edit", task_id=t.id),
                }
            )

        for p in (
            Preventivo.query.filter(Preventivo.descrizione.ilike(pattern))
            .limit(2)
            .all()
        ):
            results.append(
                {
                    "type": "preventivo",
                    "id": p.id,
                    "label": p.descrizione,
                    "subtitle": p.cliente.name if p.cliente else "",
                    "icon": "bi-receipt",
                    "url": url_for("visualizza_preventivo", id=p.id),
                }
            )

        for m in (
            FinancialMovement.query.filter(
                db.or_(
                    FinancialMovement.title.ilike(pattern),
                    FinancialMovement.description.ilike(pattern),
                )
            )
            .limit(2)
            .all()
        ):
            results.append(
                {
                    "type": "finance",
                    "id": m.id,
                    "label": m.title,
                    "subtitle": f"{m.movement_type} \u00b7 {m.amount}\u20ac",
                    "icon": "bi-cash-coin",
                    "url": url_for("finance.finance_edit", movement_id=m.id),
                }
            )

        for e in (
            EditorialPublication.query.filter(
                db.or_(
                    EditorialPublication.title.ilike(pattern),
                    EditorialPublication.caption.ilike(pattern),
                    EditorialPublication.internal_notes.ilike(pattern),
                )
            )
            .limit(2)
            .all()
        ):
            results.append(
                {
                    "type": "editoriale",
                    "id": e.id,
                    "label": e.title,
                    "subtitle": e.cliente.name if e.cliente else "",
                    "icon": "bi-calendar2-week",
                    "url": url_for(
                        "editorial_calendar.editorial_edit", publication_id=e.id
                    ),
                }
            )

        for ev in (
            CalendarEvent.query.filter(
                db.or_(
                    CalendarEvent.title.ilike(pattern),
                    CalendarEvent.description.ilike(pattern),
                )
            )
            .limit(2)
            .all()
        ):
            results.append(
                {
                    "type": "calendario",
                    "id": ev.id,
                    "label": ev.title,
                    "subtitle": ev.start_datetime.strftime("%d/%m/%Y %H:%M")
                    if ev.start_datetime
                    else "",
                    "icon": "bi-calendar3",
                    "url": url_for("calendar.calendar_edit", event_id=ev.id),
                }
            )

        for mb in (
            Moodboard.query.filter(
                db.or_(
                    Moodboard.title.ilike(pattern),
                    Moodboard.description.ilike(pattern),
                )
            )
            .limit(2)
            .all()
        ):
            results.append(
                {
                    "type": "moodboard",
                    "id": mb.id,
                    "label": mb.title,
                    "subtitle": mb.cliente.name if mb.cliente else "",
                    "icon": "bi-images",
                    "url": url_for("moodboards.moodboard_detail", id=mb.id),
                }
            )

    return jsonify({"results": results})
