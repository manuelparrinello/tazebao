from datetime import datetime

from flask import Blueprint, current_app, flash, g, redirect, render_template, request, url_for

from ..auth import login_required, role_required
from ..extensions import db
from ..models import EMAIL_DIRECTIONS, Cliente, EmailLog, Lavoro, Task
from ..utils.parsing import parse_optional_datetime, parse_optional_id


bp = Blueprint("emails", __name__)


def email_form_choices():
    return {
        "directions": EMAIL_DIRECTIONS,
        "clienti": Cliente.query.order_by(Cliente.name.asc()).all(),
        "lavori": Lavoro.query.order_by(Lavoro.descrizione.asc()).all(),
        "tasks": Task.query.order_by(Task.updated_at.desc(), Task.created_at.desc()).all(),
    }


def apply_email_form(email_log):
    email_log.subject = (request.form.get("subject") or "").strip()
    email_log.body = (request.form.get("body") or "").strip() or None
    email_log.direction = request.form.get("direction") or "outbound"
    email_log.email_address = (request.form.get("email_address") or "").strip().lower()
    email_log.cliente_id = parse_optional_id(request.form.get("cliente_id"))
    email_log.lavoro_id = parse_optional_id(request.form.get("lavoro_id"))
    email_log.task_id = parse_optional_id(request.form.get("task_id"))
    email_log.sent_at = parse_optional_datetime(request.form.get("sent_at"))

    if not email_log.subject:
        raise ValueError("L'oggetto e obbligatorio.")
    if email_log.direction not in EMAIL_DIRECTIONS:
        raise ValueError("Direzione comunicazione non valida.")
    if not email_log.email_address:
        raise ValueError("L'indirizzo email e obbligatorio.")
    if email_log.sent_at is None:
        raise ValueError("La data comunicazione e obbligatoria.")


@bp.get("/emails")
@login_required
def emails_index():
    query = EmailLog.query
    search = (request.args.get("q") or "").strip()

    if search:
        pattern = f"%{search}%"
        query = query.outerjoin(Cliente).filter(
            db.or_(
                EmailLog.email_address.ilike(pattern),
                EmailLog.subject.ilike(pattern),
                Cliente.name.ilike(pattern),
                Cliente.ragsoc.ilike(pattern),
            )
        )

    email_logs = query.order_by(EmailLog.sent_at.desc(), EmailLog.id.desc()).all()
    return render_template("emails.html", email_logs=email_logs, search=search)


@bp.route("/emails/new", methods=["GET", "POST"])
@role_required("admin", "operatore")
def emails_new():
    email_log = EmailLog(
        direction="outbound",
        sent_at=datetime.now(),
        cliente_id=request.args.get("cliente_id", type=int),
    )
    error = None

    if request.method == "POST":
        try:
            email_log.created_by = g.current_user.id if g.get("current_user") else None
            apply_email_form(email_log)
            db.session.add(email_log)
            db.session.commit()
            return redirect(url_for("emails.emails_index"))
        except ValueError as exc:
            db.session.rollback()
            error = str(exc)

    return render_template(
        "email_form.html",
        email_log=email_log,
        error=error,
        form_action=url_for("emails.emails_new"),
        page_title="Nuova comunicazione",
        submit_label="Registra comunicazione",
        **email_form_choices(),
    )


@bp.route("/emails/<int:email_id>/edit", methods=["GET", "POST"])
@role_required("admin", "operatore")
def emails_edit(email_id):
    email_log = EmailLog.query.get_or_404(email_id)
    error = None

    if request.method == "POST":
        try:
            apply_email_form(email_log)
            db.session.commit()
            return redirect(url_for("emails.emails_index"))
        except ValueError as exc:
            db.session.rollback()
            error = str(exc)

    return render_template(
        "email_form.html",
        email_log=email_log,
        error=error,
        form_action=url_for("emails.emails_edit", email_id=email_log.id),
        page_title="Modifica comunicazione",
        submit_label="Salva modifiche",
        **email_form_choices(),
    )


@bp.post("/emails/<int:email_id>/delete")
@role_required("admin", "operatore")
def emails_delete(email_id):
    email_log = EmailLog.query.get_or_404(email_id)
    try:
        db.session.delete(email_log)
        db.session.commit()
        flash("Comunicazione eliminata con successo.", "success")
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Errore eliminazione email log %d", email_id)
        flash("Impossibile eliminare la comunicazione. Operazione annullata.", "danger")
    return redirect(url_for("emails.emails_index"))
