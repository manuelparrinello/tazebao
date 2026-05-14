from flask import Blueprint, current_app, render_template, request

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
